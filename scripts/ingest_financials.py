import os
import sqlite3
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "financials.db"

TICKERS = ["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "WMT", "META", "TSLA", "JPM"]

def create_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_profiles (
        ticker TEXT PRIMARY KEY,
        name TEXT,
        sector TEXT,
        industry TEXT,
        market_cap REAL,
        description TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS annual_financials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        fiscal_year INTEGER,
        total_revenue REAL,
        gross_profit REAL,
        operating_income REAL,
        net_income REAL,
        operating_cash_flow REAL,
        free_cash_flow REAL,
        total_assets REAL,
        total_liabilities REAL,
        total_equity REAL,
        gross_margin REAL,
        operating_margin REAL,
        net_margin REAL,
        pe_ratio REAL,
        roe REAL,
        eps REAL,
        UNIQUE(ticker, fiscal_year)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        returns REAL,
        UNIQUE(ticker, date)
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fin_ticker_year ON annual_financials(ticker, fiscal_year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker_date ON daily_prices(ticker, date);")
    conn.commit()

def populate_database():
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    cursor = conn.cursor()

    for ticker in TICKERS:
        print(f"\n---> Ingesting data for {ticker}...")
        stock = yf.Ticker(ticker)
        
        # 1. Company Profile
        try:
            info = stock.info
            name = info.get("shortName") or info.get("longName") or ticker
            sector = info.get("sector", "Unknown")
            industry = info.get("industry", "Unknown")
            market_cap = info.get("marketCap", 0.0)
            desc = (info.get("longBusinessSummary") or "")[:400]
            
            cursor.execute("""
            INSERT OR REPLACE INTO company_profiles (ticker, name, sector, industry, market_cap, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (ticker, name, sector, industry, market_cap, desc))
        except Exception as e:
            print(f"  Warning: failed profile for {ticker}: {e}")

        # 2. Annual Financial Statements
        try:
            fin = stock.financials
            bs = stock.balance_sheet
            cf = stock.cashflow
            
            years = set()
            if not fin.empty:
                years.update([col.year for col in fin.columns if hasattr(col, "year")])
            
            for y in sorted(years)[-5:]:  # Last 5 available fiscal years
                try:
                    # Find matching date column
                    matching_cols = [c for c in fin.columns if hasattr(c, "year") and c.year == y]
                    if not matching_cols:
                        continue
                    col = matching_cols[0]
                    
                    revenue = float(fin.loc["Total Revenue", col]) if "Total Revenue" in fin.index else 0.0
                    gross_profit = float(fin.loc["Gross Profit", col]) if "Gross Profit" in fin.index else 0.0
                    op_income = float(fin.loc["Operating Income", col]) if "Operating Income" in fin.index else 0.0
                    net_income = float(fin.loc["Net Income", col]) if "Net Income" in fin.index else 0.0
                    
                    # Cash flow items
                    op_cf = 0.0
                    if not cf.empty and col in cf.columns:
                        if "Operating Cash Flow" in cf.index:
                            op_cf = float(cf.loc["Operating Cash Flow", col])
                        elif "Operating Activities" in cf.index:
                            op_cf = float(cf.loc["Operating Activities", col])
                    
                    fcf = 0.0
                    if not cf.empty and col in cf.columns and "Free Cash Flow" in cf.index:
                        fcf = float(cf.loc["Free Cash Flow", col])
                    else:
                        fcf = op_cf * 0.7  # approximate if missing
                    
                    # Balance sheet items
                    assets = 0.0
                    liabilities = 0.0
                    equity = 0.0
                    if not bs.empty and col in bs.columns:
                        if "Total Assets" in bs.index:
                            assets = float(bs.loc["Total Assets", col])
                        if "Total Liabilities Net Minority Interest" in bs.index:
                            liabilities = float(bs.loc["Total Liabilities Net Minority Interest", col])
                        if "Stockholders Equity" in bs.index:
                            equity = float(bs.loc["Stockholders Equity", col])
                    
                    if equity == 0.0 and assets > 0:
                        equity = assets - liabilities
                    
                    gross_margin = (gross_profit / revenue) if revenue else 0.0
                    op_margin = (op_income / revenue) if revenue else 0.0
                    net_margin = (net_income / revenue) if revenue else 0.0
                    roe = (net_income / equity) if equity else 0.0
                    
                    pe_ratio = float(info.get("trailingPE", 25.0) or 25.0)
                    eps = float(info.get("trailingEps", 0.0) or 0.0)
                    
                    cursor.execute("""
                    INSERT OR REPLACE INTO annual_financials (
                        ticker, fiscal_year, total_revenue, gross_profit, operating_income,
                        net_income, operating_cash_flow, free_cash_flow, total_assets,
                        total_liabilities, total_equity, gross_margin, operating_margin,
                        net_margin, pe_ratio, roe, eps
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker, int(y), revenue, gross_profit, op_income,
                        net_income, op_cf, fcf, assets, liabilities, equity,
                        round(gross_margin, 4), round(op_margin, 4), round(net_margin, 4),
                        round(pe_ratio, 2), round(roe, 4), round(eps, 2)
                    ))
                    print(f"  Inserted financials: {ticker} ({y}): Rev=${revenue:,.0f}, NetInc=${net_income:,.0f}")
                except Exception as ex:
                    print(f"  Error processing year {y} for {ticker}: {ex}")

        except Exception as e:
            print(f"  Warning: financial statements error for {ticker}: {e}")

        # 3. Daily Stock Prices (1 Year history)
        try:
            hist = stock.history(period="1y")
            if not hist.empty:
                hist["returns"] = hist["Close"].pct_change()
                for dt, row in hist.iterrows():
                    date_str = dt.strftime("%Y-%m-%d")
                    cursor.execute("""
                    INSERT OR REPLACE INTO daily_prices (
                        ticker, date, open, high, low, close, volume, returns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker, date_str,
                        round(float(row["Open"]), 2),
                        round(float(row["High"]), 2),
                        round(float(row["Low"]), 2),
                        round(float(row["Close"]), 2),
                        int(row["Volume"]),
                        round(float(row["returns"]) if not np.isnan(row["returns"]) else 0.0, 5)
                    ))
                print(f"  Inserted {len(hist)} daily price records for {ticker}.")
        except Exception as e:
            print(f"  Warning: historical price error for {ticker}: {e}")

    conn.commit()
    conn.close()
    print("\nDatabase initialization complete! Saved to:", DB_PATH)

if __name__ == "__main__":
    populate_database()
