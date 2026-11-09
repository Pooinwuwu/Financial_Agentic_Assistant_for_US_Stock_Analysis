import os
import re
import ast
import io
import sqlite3
import pathlib
import contextlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stocks.db"

# 1. อนุญาตเฉพาะโมดูลที่ปลอดภัย (Whitelist)
ALLOWED_MODULES = {"math", "numpy", "pandas", "sqlite3"}
BANNED_MODULES = {"os", "sys", "subprocess", "shutil", "socket", "requests", "urllib", "importlib", "pathlib"}
BANNED_FUNCTIONS = {"eval", "exec", "compile", "open"}

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """ฟังก์ชัน Custom __import__ บังคับให้นำเข้าได้เฉพาะ Whitelisted Modules"""
    base_module = name.split('.')[0]
    if base_module in ALLOWED_MODULES:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Refused: Importing module '{name}' is strictly forbidden in sandbox.")

def inspect_python_ast(code_str: str) -> str | None:
    """ตรวจสอบ AST (Abstract Syntax Tree) ป้องกันคำสั่งอันตราย"""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return f"SyntaxError in Python code: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split('.')[0] in BANNED_MODULES:
                    return f"Refused: Importing module '{alias.name}' is strictly forbidden."
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in BANNED_MODULES:
                return f"Refused: Importing from module '{node.module}' is strictly forbidden."
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BANNED_FUNCTIONS:
                return f"Refused: Function '{node.func.id}()' is strictly forbidden."

    return None

def clean_python_code(code_text: str) -> str:
    """สกัดเฉพาะโค้ด Python จาก Markdown Fences"""
    if not code_text:
        return ""
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", code_text, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = code_text.replace("```", "")
    return cleaned.strip()

def execute_sandboxed_python(code_str: str, db_path: pathlib.Path = DEFAULT_DB_PATH) -> dict:
    """รันโค้ด Python ในสภาพแวดล้อมที่จำกัดขอบเขตอย่างปลอดภัย"""
    cleaned_code = clean_python_code(code_str)
    ast_error = inspect_python_ast(cleaned_code)
    if ast_error:
        raise ValueError(ast_error)

    import math
    import numpy as np
    import pandas as pd

    safe_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "zip": zip,
            "sum": sum,
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
            "enumerate": enumerate,
            "sorted": sorted,
            "isinstance": isinstance,
            "__import__": safe_import,  # 📌 เพิ่ม safe_import ป้องกัน error
        },
        "math": math,
        "np": np,
        "pd": pd,
        "sqlite3": sqlite3,
        "DB_PATH": str(db_path.resolve())
    }

    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        exec(cleaned_code, safe_globals)

    output = stdout_buffer.getvalue().strip()
    return {
        "status": "success",
        "output": output if output else "Execution completed with no printed output.",
        "executed_code": cleaned_code
    }

def run_python_calc(user_question: str, db_path: pathlib.Path = DEFAULT_DB_PATH, max_retries: int = 2) -> dict:
    """ฟังก์ชันหลัก: LLM เขียนสคริปต์ Python -> Guardrail AST -> Execute -> Repair Loop"""
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    system_prompt = f"""You are a Python Data Analyst & Financial Statistician.
Write clean Python code to answer the user's financial math or statistical analysis question.

Environment Details:
- SQLite Database is located at: `DB_PATH`
- Pre-imported available objects: `math`, `np` (numpy), `pd` (pandas), `sqlite3`, `DB_PATH`
- Tables in DB:
  1. `companies` (symbol, company_name, sector, market_cap)
  2. `financials` (symbol, year, revenue, net_income, net_margin, eps, pe_ratio)
  3. `daily_prices` (symbol, date, open, high, low, close, volume)

Rules:
1. Return ONLY executable Python code inside ```python ... ``` fences.
2. ALWAYS use `print()` to output final numerical results or statistical summaries.
3. You can connect to SQLite DB using `conn = sqlite3.connect(DB_PATH)`.
4. Do NOT import forbidden modules (`os`, `sys`, `subprocess`, `requests`).
"""

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

        if not response.choices[0]:
            raise ValueError("LLM returned empty choices list.")

        raw_code = response.choices[0].message.content
        if not raw_code:
            raise ValueError("LLM returned empty code content.")

        try:
            result = execute_sandboxed_python(raw_code, db_path=db_path)
            return result
        except Exception as e:
            error_msg = str(e)
            if attempt == max_retries:
                raise RuntimeError(f"Python execution failed after {max_retries} retries. Error: {error_msg}")

            messages.append({"role": "assistant", "content": raw_code})
            messages.append({
                "role": "user", 
                "content": f"The executed Python code failed with error:\n{error_msg}\nPlease fix the code and ensure it prints the final answer."
            })