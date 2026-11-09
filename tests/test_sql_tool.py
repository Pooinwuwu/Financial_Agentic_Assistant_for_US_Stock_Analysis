import pathlib
from src.tools.sql_tool import text_to_sql

# ทดสอบคำถามภาษาธรรมชาติ
questions = [
    "ขอรายชื่อหุ้น 3 อันดับแรกที่มีรายได้ (revenue) สูงสุดในปี 2025",
    "ขอราคาปิด (close) ล่าสุดของหุ้น NVDA",
    "เปรียบเทียบ P/E ratio ของหุ้นในกลุ่ม Technology"
]

for q in questions:
    print(f"\n❓ คำถาม: {q}")
    try:
        res = text_to_sql(q)
        print(f"💻 SQL ที่สร้าง: {res['sql']}")
        print(f"📊 คอลัมน์: {res['columns']}")
        print(f"📈 ผลลัพธ์ ({len(res['rows'])} แถว):")
        for row in res['rows'][:3]:
            print(f"   {row}")
    except Exception as err:
        print(f"❌ เกิดข้อผิดพลาด: {err}")