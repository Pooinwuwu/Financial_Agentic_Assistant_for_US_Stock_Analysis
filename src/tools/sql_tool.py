import os
import re
import sqlite3
import pathlib
from openai import OpenAI
from dotenv import load_dotenv

# โหลดค่า OPENAI_BASE_URL และ OPENAI_API_KEY จากไฟล์ .env
load_dotenv()

# 📌 1. กำหนด Absolute Path ย้อนกลับไปหา Root Directory ของโปรเจกต์
CURRENT_FILE_PATH = pathlib.Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE_PATH.parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stocks.db"

# Regex ตรวจจับคำสั่งต้องห้าม (Denylist)
BANNED_KEYWORDS = re.compile(
    r"(?is)\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum|reindex)\b"
)

def get_schema_prompt(db_path: pathlib.Path) -> str:
    """ดึง DDL จากฐานข้อมูล SQLite มาสร้างเป็น System Prompt พร้อมระบุ Schema ที่ชัดเจน"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables_sql = cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL;"
    ).fetchall()
    conn.close()
    
    # ดึงเฉพาะข้อความ SQL ใน tuple index [0] ป้องกันติดวงเล็บ tuple
    schema_str = "\n\n".join(row[0] for row in tables_sql if row and row[0])
    
    return f"""You are a SQLite expert. Convert natural language questions into valid, single-statement SQLite SELECT queries.

Database DDL Schema:
{schema_str}

Valid Tables in Database:
1. `companies` (symbol, company_name, sector, industry, market_cap)
2. `financials` (symbol, year, quarter, period_type, revenue, net_income, operating_income, gross_margin, net_margin, eps, pe_ratio, roe, free_cash_flow)
3. `daily_prices` (symbol, date, open, high, low, close, adj_close, volume)

Rules:
1. Return ONLY the SQL query inside ```sql ... ``` fences.
2. Use ONLY SELECT or WITH statements. Never attempt to modify data.
3. Use ONLY table names from the schema above (`companies`, `financials`, `daily_prices`). NEVER use invented table names like `stock`, `stocks`, `symbol`, or `financial`.
4. Use JOIN on `symbol` when querying across multiple tables.
5. Keep column names exact according to the schema.
"""

def clean_sql(sql_text: str) -> str:
    """แกะคำสั่ง SQL จาก markdown fences อย่างปลอดภัย"""
    if not sql_text:
        return ""
    
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", sql_text, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = sql_text.replace("```", "")
    
    cleaned = cleaned.strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].strip()
        
    return cleaned.rstrip(";").strip()

def guard_sql(sql: str) -> str | None:
    """ตรวจสอบ Guardrails ความปลอดภัยของคำสั่ง SQL"""
    if not re.match(r"(?is)^\s*(select|with)\b", sql):
        return "Refused: Query must start with SELECT or WITH."
    if ";" in sql:
        return "Refused: Multiple statements are not allowed."
    if BANNED_KEYWORDS.search(sql):
        return "Refused: Query contains banned data modification keywords."
    return None

def add_limit_if_missing(sql: str, default_limit: int = 100) -> str:
    """เติม LIMIT ให้อัตโนมัติหากไม่มีการระบุมา"""
    if not re.search(r"(?is)\blimit\s+\d+", sql):
        return f"{sql} LIMIT {default_limit}"
    return sql

def execute_sql(db_path: pathlib.Path, query: str) -> dict:
    """รันคำสั่ง SQL กับฐานข้อมูลแบบ Read-Only"""
    cleaned = clean_sql(query)
    guard_error = guard_sql(cleaned)
    if guard_error:
        raise ValueError(guard_error)
    
    final_sql = add_limit_if_missing(cleaned)
    
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    try:
        cursor.execute(final_sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return {"columns": columns, "rows": rows, "sql": final_sql}
    finally:
        conn.close()

def text_to_sql(user_question: str, db_path: pathlib.Path = pathlib.Path("data/stocks.db"), max_retries: int = 2) -> dict:
    """ฟังก์ชันหลักแปลงคำถามภาษาธรรมชาติเป็น SQL"""
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    system_prompt = get_schema_prompt(db_path)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]
    
    for attempt in range(max_retries + 1):
        response = client.chat.completions.create(
            model="gemma-4-E4B-it",
            messages=messages,
            temperature=0
        )
        
        if not response.choices:
            raise ValueError("LLM returned an empty response choices list.")
            
        raw_sql = response.choices[0].message.content
        if not raw_sql:
            raise ValueError("LLM returned empty message content.")
        
        try:
            result = execute_sql(db_path, raw_sql)
            return result
        except (ValueError, sqlite3.OperationalError) as e:
            error_msg = str(e)
            if attempt == max_retries:
                raise RuntimeError(f"Text-to-SQL failed after {max_retries} retries. Error: {error_msg}")
            
            messages.append({"role": "assistant", "content": raw_sql})
            messages.append({"role": "user", "content": f"The generated SQL query failed with error: {error_msg}. Please generate a corrected SQL query using ONLY existing tables (companies, financials, daily_prices)."})