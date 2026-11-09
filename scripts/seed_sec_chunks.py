import os
import json
import sqlite3
import pathlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "stocks.db"

# 1. โครงสร้าง DDL ตาราง sec_chunks
CREATE_SEC_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS sec_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    FOREIGN KEY (symbol) REFERENCES companies (symbol)
);
"""

# 2. ข้อมูลตัวอย่าง SEC Form 10-K (Item 1A: Risk Factors และ Item 7: MD&A)
SAMPLE_SEC_DATA = [
    {
        "symbol": "NVDA",
        "year": 2024,
        "section": "Item 1A",
        "text": "NVIDIA faces intense competition in GPU and AI accelerators from semiconductor vendors and tech giants. Global supply chain constraints, export controls, and regulatory compliance regarding advanced AI chips present significant operational risks."
    },
    {
        "symbol": "NVDA",
        "year": 2024,
        "section": "Item 7",
        "text": "Management Discussion: Fiscal year 2024 revenue reached record levels driven by massive demand for Data Center H100 and A100 AI platforms. Gross margins expanded significantly due to favorable product mix."
    },
    {
        "symbol": "AAPL",
        "year": 2024,
        "section": "Item 7",
        "text": "Management Discussion: Gross margin for FY2024 remained strong at 45.2%, supported by growth in high-margin Services revenue and supply chain cost efficiency across hardware lineups."
    },
    {
        "symbol": "MSFT",
        "year": 2024,
        "section": "Item 1A",
        "text": "Microsoft identifies cybersecurity threats, data privacy compliance, operational availability of Azure cloud infrastructure, and rapid AI model developments as key business risk factors."
    }
]

def get_embedding(text: str, client: OpenAI) -> list[float]:
    """คำนวณ เวกเตอร์ bge-m3 (1024 มิติ)"""
    resp = client.embeddings.create(
        model="bge-m3",
        input=[text]
    )
    return resp.data[0].embedding

def init_and_seed_sec_chunks():
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # สร้างตาราง sec_chunks
    cursor.execute(CREATE_SEC_CHUNKS_TABLE)
    print("✅ สร้างตาราง sec_chunks สำเร็จ")
    
    # แปลง Text -> bge-m3 Embedding -> บันทึกลง DB
    print("⏳ กำลังสร้าง Vector Embeddings และบันทึกข้อมูล SEC 10-K...")
    records = []
    for item in SAMPLE_SEC_DATA:
        emb = get_embedding(item["text"], client)
        records.append((
            item["symbol"],
            item["year"],
            item["section"],
            item["text"],
            json.dumps(emb)  # เก็บ Embedding Vector เป็น JSON string
        ))
    
    cursor.executemany(
        "INSERT INTO sec_chunks (symbol, year, section, chunk_text, embedding_json) VALUES (?, ?, ?, ?, ?)",
        records
    )
    conn.commit()
    conn.close()
    print(f"🎉 นำเข้าข้อมูล sec_chunks เรียบร้อยแล้ว {len(records)} รายการ")

if __name__ == "__main__":
    init_and_seed_sec_chunks()