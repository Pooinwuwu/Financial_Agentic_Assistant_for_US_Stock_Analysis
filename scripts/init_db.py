# 1 import module and connection
import sqlite3
import pathlib

db_path = pathlib.Path("data/stocks.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON;")

# 2 define command sql for table
create_schema_sql = """
CREATE TABLE IF NOT EXISTS companies (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    industry TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    year INTEGER NOT NULL,
    quarter INTEGER,
    period_type TEXT CHECK(period_type IN ('annual', 'quarterly')),
    revenue REAL,
    net_income REAL,
    operating_income REAL,
    gross_margin REAL,
    net_margin REAL,
    eps REAL,
    pe_ratio REAL,
    roe REAL,
    free_cash_flow REAL,
    FOREIGN KEY (symbol) REFERENCES companies(symbol),
    UNIQUE(symbol, year, quarter, period_type)
);

CREATE TABLE IF NOT EXISTS daily_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT, 
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    FOREIGN KEY (symbol) REFERENCES companies(symbol),
    UNIQUE(symbol, date)
);

-- create indexes for booster speed query
CREATE INDEX idx_financials_symbol_year_period_type
ON financials (symbol, year, period_type);

CREATE INDEX idx_daily_prices_symbol_date
ON daily_prices (symbol, date);
"""
# insert name companies
companies_data = [
    ('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics'),
    ('MSFT', 'Microsoft Corp.', 'Technology', 'Software — Infrastructure'),
    ('NVDA', 'NVIDIA Corp.', 'Technology', 'Semiconductors'),
    ('AMD', 'Advanced Micro Devices Inc.', 'Technology', 'Semiconductors'),
    ('GOOGL', 'Alphabet Inc.', 'Communication Services', 'Internet Content & Information'),
    ('AMZN', 'Amazon.com, Inc.', 'Consumer Cyclical', 'Internet Retail'),
    ('WMT', 'Walmart Inc.', 'Consumer Defensive', 'Discount Stores'),
    ('META', 'Meta Platforms Inc.', 'Communication Services', 'Internet Content & Information'),
    ('TSLA', 'Tesla Inc.', 'Consumer Cyclical', 'Auto Manufacturers'),
    ('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 'Banks — Diversified')
]

# command insert ready? 
insert_sql = """
INSERT OR REPLACE INTO companies (symbol, company_name, sector, industry)
VALUES (?, ?, ?, ?);
"""

# 3 Run sql command and save
conn.executescript(create_schema_sql)

# 4 INSERT data whole 10 rows in once.
conn.executemany(insert_sql, companies_data)


conn.commit()
conn.close()
