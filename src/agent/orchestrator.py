import os
import json
import pathlib
from openai import OpenAI
from dotenv import load_dotenv

from src.tools.sql_tool import text_to_sql
from src.tools.vector_tool import sec_doc_rag
from src.tools.calc_tool import run_python_calc

load_dotenv()

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "stocks.db"

# 1. นิยาม JSON Schema สำหรับ Native Tool Calling
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute read-only SQL queries on historical financial metrics (revenue, net_income, eps, pe_ratio, daily_prices) for 10 US stocks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {"type": "string", "description": "The question to generate SQL for."}
                },
                "required": ["user_question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sec_doc_rag",
            "description": "Search SEC Form 10-K filings (Item 1A Risk Factors & Item 7 MD&A) for qualitative business insights and citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {"type": "string", "description": "The search query regarding company risks or management discussion."}
                },
                "required": ["user_question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_calc",
            "description": "Execute sandboxed Python script for statistical calculations (mean, volatility, growth rate) and data analysis on stocks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_question": {"type": "string", "description": "The mathematical or statistical calculation question."}
                },
                "required": ["user_question"]
            }
        }
    }
]

def dispatch_tool(tool_name: str, tool_args: dict, db_path: pathlib.Path = DEFAULT_DB_PATH) -> str:
    """ฟังก์ชัน Dispatcher เรียกใช้เครื่องมือจริง และ คืนค่ากลับเป็น String"""
    user_q = tool_args.get("user_question", "")
    try:
        if tool_name == "run_sql":
            res = text_to_sql(user_q, db_path=db_path)
            return json.dumps({"status": "success", "sql_used": res["sql"], "columns": res["columns"], "rows": res["rows"]}, ensure_ascii=False)
        elif tool_name == "sec_doc_rag":
            res = sec_doc_rag(user_q, db_path=db_path)
            return json.dumps(res, ensure_ascii=False)
        elif tool_name == "run_python_calc":
            res = run_python_calc(user_q, db_path=db_path)
            return json.dumps(res, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

def run_agent_orchestrator(user_question: str, db_path: pathlib.Path = DEFAULT_DB_PATH, max_steps: int = 4) -> str:
    """
    Agent Decision Loop (Observe-Think-Act):
    - ควบคุมการตัดสินใจของ Gemma-4-E4B-it
    - รองรับ Multi-Hop Workflow และมี Step Cap ป้องกัน Infinite Loop
    """
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )

    system_prompt = """You are an expert Financial Agentic Assistant for 10 US stocks.
Answer the user's question accurately. You have access to 3 tools: `run_sql`, `sec_doc_rag`, and `run_python_calc`.

Rules:
1. For general greetings or non-financial chit-chat, answer directly WITHOUT calling tools.
2. For quantitative metrics or prices, call `run_sql`.
3. For qualitative risks, Item 1A, or Item 7 MD&A in 10-K filings, call `sec_doc_rag` and ALWAYS cite sources.
4. For complex statistical calculations or time-series analysis, call `run_python_calc`.
5. For multi-step questions, call the required tools sequentially to gather complete evidence before summarizing your final answer.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gemma-4-E4B-it",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0  # Deterministic control flow
        )

        msg = response.choices[0].message

        # หาก LLM ไม่ได้สั่งเรียก Tool ถือเป็นคำตอบสุดท้าย (Natural Stop)
        if not msg.tool_calls:
            return msg.content

        # หาก LLM สั่งเรียก Tool (Act Phase)
        messages.append(msg)  # บันทึก Assistant Call เข้า Conversation History

        for tool_call in msg.tool_calls:
            call_id = tool_call.id
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Observe Phase: รัน Tool และส่งผลลัพธ์กลับในฐานะ role: "tool"
            tool_result = dispatch_tool(func_name, args, db_path=db_path)
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": tool_result
            })

    return "ขออภัย ระบบดำเนินการเกินจำนวนขั้นตอนสูงสุด (max_steps) กรุณาระบุคำถามให้กระชับขึ้น"