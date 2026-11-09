import sys
import pathlib

# เพิ่ม Root Directory เข้า sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.tools.calc_tool import run_python_calc

questions = [
    "คำนวณค่าเฉลี่ย (Mean) และความผันผวน (Volatility/Standard Deviation) ของราคาปิดหุ้น NVDA จากตาราง daily_prices",
    "คำนวณอัตราส่วน Net Margin เฉลี่ยของบริษัทในกลุ่ม Technology ในตาราง financials"
]

for q in questions:
    print(f"\n❓ คำถาม: {q}")
    try:
        res = run_python_calc(q)
        print("💻 โค้ด Python ที่สร้างขึ้น:")
        print(res["executed_code"])
        print("\n📈 ผลลัพธ์การคำนวณ (Stdout):")
        print(res["output"])
    except Exception as err:
        print(f"❌ เกิดข้อผิดพลาด: {err}")