import sqlite3
import pathlib

db_path = pathlib.Path("data/stocks.db")

if not db_path.exists():
    print("❌ ไม่พบไฟล์ฐานข้อมูล data/stocks.db กรุณารัน init_db.py และ seed_data.py ก่อน")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("==========================================")
print("📊 สรุปจำนวนข้อมูลในฐานข้อมูล data/stocks.db")
print("==========================================")

#1 check number of row in table
tables = ['companies', 'financials', 'daily_prices']
for table in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f" ตาราง {table:<15}: {count:,} แถว")

print("\n==========================================")
print("🔍 ตัวอย่างข้อมูลในแต่ละตาราง")
print("==========================================")

#2 Example financials table
print("\n[1] ตาราง companies (3 first list)")
companies_sample = cursor.execute("SELECT symbol, company_name, sector, industry FROM companies LIMIT 3").fetchall()
for row in companies_sample:
    print(f"   -{row[0]}: {row[1]} | {row[2]} ({row[3]})")

# 3. ดูตัวอย่างตาราง financials
print("\n[2] ตาราง financials (3 รายการแรก):")
financials_sample = cursor.execute(
    "SELECT symbol, year, revenue, net_income, net_margin, eps FROM financials LIMIT 3"
).fetchall()
for row in financials_sample:
    rev_b = row[2] / 1e9 if row[2] else 0  # แปลงเป็นพันล้านดอลลาร์
    net_b = row[3] / 1e9 if row[3] else 0
    print(f"   - {row[0]} ({row[1]}): Revenue = ${rev_b:.2f}B | Net Income = ${net_b:.2f}B | Net Margin = {row[4]:.2f}% | EPS = ${row[5]}")

# 4. ดูตัวอย่างตาราง daily_prices
print("\n[3] ตาราง daily_prices (ราคาล่าสุด 3 รายการแรก):")
prices_sample = cursor.execute(
    "SELECT symbol, date, open, close, volume FROM daily_prices ORDER BY date DESC LIMIT 3"
).fetchall()
for row in prices_sample:
    print(f"   - {row[0]} ({row[1]}): Open = ${row[2]:.2f} | Close = ${row[3]:.2f} | Volume = {row[4]:,}")

conn.close()
print("\n✅ ตรวจสอบข้อมูลเสร็จสิ้น!")