import yfinance
import sqlite3
import datetime 
import pathlib

db_path = pathlib.Path("data/stocks.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON;")

display_companies = """
    SELECT symbol FROM companies;
"""
symbols = [row[0] for row in conn.execute(display_companies).fetchall()]

financials_rows = []
prices_rows = []

for symbol in symbols:
    # สร้าง ticker object for each a stock
    ticker = yfinance.Ticker(symbol)
    # ดึงงบการเงิน
    fin = ticker.financials
    # ดึงชื่อ column ปีล่าสุด
    lastest_col = fin.columns[0]
    # ดึงตัวเลขจาก ปี
    year = lastest_col.year

    # ดึงรายได้รวม Total revenue
    revenue = fin.loc['Total Revenue', lastest_col] if 'Total Revenue' in fin.index else 0.0
    # ดึงกำไรสุทธิ Net Income
    net_income = fin.loc['Net Income', lastest_col] if 'Net Income' in fin.index else 0.0
    # ดึงกำไรจากการดำเนินงาน Operating Income
    operating_income = fin.loc['Operating Income', lastest_col] if 'Operating Income' in fin.index else 0.0

    # calculate Net Margin %
    net_margin = (net_income / revenue * 100) if revenue else 0.0

    # calculate gross margin %
    gross_profit = fin.loc['Gross Profit', lastest_col] if 'Gross Profit' in fin.index else 0.0
    gross_margin = (gross_profit / revenue * 100) if revenue else 0.0

    eps = ticker.info.get('trailingEps', 0.0)
    pe_ratio = ticker.info.get('trailingPE', 0.0)
    roe = ticker.info.get('returnOnEquity', 0.0)
    
    cf = ticker.cashflow
    cash_flow = cf.loc['Free Cash Flow', cf.columns[0]] if (not cf.empty and 'Free Cash Flow' in cf.index) else 0.0

    # บันทึกตัวเลขการเงินใส่ financials_rows
    financials_rows.append((
        symbol, year, None, 'annual',
        float(revenue), float(net_income), float(operating_income),
        float(gross_margin), float(net_margin),
        float(eps), float(pe_ratio), float(roe), float(cash_flow)
    ))

    # ดึงราคาหุ้นรายวันย้อนหลัง 90 วันใส่ prices_rows
    hist = ticker.history(period='90d')
    for date, row in hist.iterrows():
        date_str = date.strftime('%Y-%m-%d')
        prices_rows.append((
            symbol, date_str,
            float(row['Open']), float(row['High']), float(row['Low']),
            float(row['Close']), float(row['Close']), int(row['Volume'])
        ))

# บันทึก ข้อมูลลงตารางการเงิน งบการเงิน
sql_financials = """
INSERT OR REPLACE INTO financials (
    symbol, year, quarter, period_type,
    revenue, net_income, operating_income,
    gross_margin, net_margin, eps, pe_ratio, roe, free_cash_flow
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

conn.executemany(sql_financials, financials_rows)
print(f"นำเข้าข้อมูล financials สำเร็จ : {len(financials_rows)} รายการ")

# 2 บันทึกข้อมูลลงตาราง daily prices ราคาหุ้นรายวัน
sql_prices = """
INSERT OR REPLACE INTO daily_prices (
    symbol, date, open, high, low, close, adj_close, volume
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);

"""

conn.executemany(sql_prices, prices_rows)
print(f'นำเข้าข้อมูล daily prices success : {len(prices_rows)} รายการ')

# save apply and close
conn.commit()
conn.close()











conn.close()
