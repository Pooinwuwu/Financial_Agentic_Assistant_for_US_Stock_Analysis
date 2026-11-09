import os
import re
import json
import sqlite3
import pathlib
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stocks.db"

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """คำนวณ Cosine Similarity ระหว่าง 2 เวกเตอร์"""
    a, b = np.array(v1), np.array(v2)
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def extract_query_metadata(user_question: str) -> dict:
    """
    ใช้ LLM สกัด Query และ Metadata Filter (symbol, year, section) จากคำถามภาษาธรรมชาติ
    """
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    system_prompt = """You are a financial query constructor.
Given a user question, extract search parameters into JSON format:
{
  "semantic_query": "core search string without stock ticker or year constraints",
  "symbol": "STOCK_TICKER or null (e.g. AAPL, NVDA, MSFT)",
  "year": integer_year_or_null,
  "section": "Item 1A" or "Item 7" or null
}

Examples:
Q: NVDA มีความเสี่ยงด้านการแข่งขันอย่างไรในปี 2024 ใน Item 1A
A: {"semantic_query": "competition risks market threats", "symbol": "NVDA", "year": 2024, "section": "Item 1A"}

Q: รายงาน MD&A ของ Apple พูดถึงปัญหาสายส่งอย่างไร
A: {"semantic_query": "supply chain issues logistics", "symbol": "AAPL", "year": null, "section": "Item 7"}
"""

    response = client.chat.completions.create(
        model="gemma-4-E4B-it",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0
    )
    
    raw_json = response.choices[0].message.content
    # Safe JSON parse
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_json, re.DOTALL | re.IGNORECASE)
    cleaned = match.group(1) if match else raw_json.replace("```", "")
    try:
        return json.loads(cleaned.strip())
    except Exception:
        return {"semantic_query": user_question, "symbol": None, "year": None, "section": None}

def get_embedding(text: str) -> list[float]:
    """ดึง เวกเตอร์ bge-m3 (1024 มิติ) ผ่าน Class Proxy"""
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    resp = client.embeddings.create(
        model="bge-m3",
        input=[text]
    )
    return resp.data[0].embedding

def sec_doc_rag(
    user_question: str, 
    db_path: pathlib.Path = DEFAULT_DB_PATH, 
    top_k: int = 4, 
    min_score: float = 0.35
) -> dict:
    """
    ฟังก์ชันหลัก RAG:
    1. Query Construction (Metadata extraction)
    2. Vector Embedding (bge-m3)
    3. Pre-filtering + Cosine Ranking
    4. Min-score Floor Filtering & Citation Formatting
    """
    # 1. สกัด Metadata Filter
    parsed = extract_query_metadata(user_question)
    query_str = parsed.get("semantic_query") or user_question
    symbol_filter = parsed.get("symbol")
    year_filter = parsed.get("year")
    section_filter = parsed.get("section")

    # 2. แปลงคำค้นหาเป็น Embedding
    query_vec = get_embedding(query_str)

    # 3. เชื่อมต่อฐานข้อมูล SQLite (หรือ pgvector) เพื่อดึง Chunk เอกสาร
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # สร้างเงื่อนไข Pre-filtering
    sql = "SELECT id, symbol, year, section, chunk_text, embedding_json FROM sec_chunks WHERE 1=1"
    params = []
    
    if symbol_filter:
        sql += " AND symbol = ?"
        params.append(symbol_filter.upper())
    if year_filter:
        sql += " AND year = ?"
        params.append(int(year_filter))
    if section_filter:
        sql += " AND section = ?"
        params.append(section_filter)

    rows = cursor.execute(sql, params).fetchall()
    conn.close()

    if not rows:
        return {
            "status": "not_found",
            "message": "ไม่พบเอกสาร SEC 10-K ที่ตรงกับเงื่อนไขการค้นหา",
            "passages": []
        }

    # 4. คำนวณ Cosine Similarity กับทุก Chunk ที่ผ่าน Pre-filter
    scored_chunks = []
    for r in rows:
        chunk_id, sym, yr, sec, text, emb_json = r
        emb = json.loads(emb_json) if isinstance(emb_json, str) else emb_json
        score = cosine_similarity(query_vec, emb)
        
        # กรองเฉพาะข้อความที่คะแนนสูงกว่า min_score floor
        if score >= min_score:
            citation = f"[{sym} 10-K ({yr}) {sec}]"
            scored_chunks.append({
                "score": round(score, 4),
                "citation": citation,
                "symbol": sym,
                "year": yr,
                "section": sec,
                "text": text
            })

    # จัดอันดับจากคะแนนมากไปน้อย (Top-K)
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_hits = scored_chunks[:top_k]

    if not top_hits:
        return {
            "status": "below_threshold",
            "message": f"พบเอกสารแต่ความเกี่ยวข้องต่ำกว่าเกณฑ์ min_score ({min_score})",
            "passages": []
        }

    return {
        "status": "success",
        "query_parsed": parsed,
        "passages": top_hits
    }