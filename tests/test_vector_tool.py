import sys
import pathlib

# เพิ่ม Root Directory เข้า sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.tools.vector_tool import sec_doc_rag

test_questions = [
    "ความเสี่ยงเรื่องข้อกำหนดทางกฎหมายและ AI ของหุ้น NVDA มีอะไรบ้าง",
    "รายงาน MD&A ของ Apple ในปี 2024 พูดถึงอัตรากำไรขั้นต้นอย่างไร"
]

for q in test_questions:
    print(f"\n❓ คำถาม: {q}")
    res = sec_doc_rag(q)
    print(f"📌 สถานะ: {res['status']}")
    if res.get("query_parsed"):
        print(f"🎯 Metadata Filter ที่สกัดได้: {res['query_parsed']}")
    print(f"📚 ผลลัพธ์ ({len(res['passages'])} passages):")
    for p in res['passages']:
        print(f"   • {p['citation']} (Score: {p['score']}) -> {p['text'][:100]}...")