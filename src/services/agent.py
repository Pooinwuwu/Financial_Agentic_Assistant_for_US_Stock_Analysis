import json
from typing import Any, Optional
from openai import OpenAI

from src.config import settings
from src.models.schemas import ChatResponse, ToolExecutionLog, Citation
from src.services.tools import TOOL_DEFINITIONS, TOOL_MAP
from src.services.guardrails import Guardrails, SecurityGuardrailError

SYSTEM_PROMPT = """You are an expert Financial Agentic Assistant specializing in equity research and financial statement analysis for 10 US equities:
Apple (AAPL), Microsoft (MSFT), NVIDIA (NVDA), AMD (AMD), Alphabet (GOOGL), Amazon (AMZN), Walmart (WMT), Meta Platforms (META), Tesla (TSLA), and JPMorgan Chase (JPM).

You have access to 4 specialized financial tools:
1. `run_sql`: Execute read-only SQL queries over historical annual financial statements (revenue, margins, net income, EPS, ROE) and daily price records. Use this for exact numbers, growth rates, margins, and comparative ratios.
2. `sec_doc_rag`: Search SEC Form 10-K filings (Item 1A Risk Factors and Item 7 MD&A) with structural metadata filters. Always use this to explain qualitative business drivers, supply chain risks, regulatory litigation, or management commentary.
3. `run_python_calc`: Run isolated Python scripts over historical daily price series (`get_prices(ticker)`) for statistical computations like annualized volatility, Sharpe ratios, moving averages, and drawdowns.
4. `search_web_news`: Retrieve recent market developments or breaking announcements for a ticker.

Guidelines:
- Quantitative queries: ALWAYS run SQL. Do not guess or hallucinate financial numbers.
- Qualitative inquiries: ALWAYS search SEC 10-K filings and cite the source passages explicitly (e.g. [NVDA_2024_Item1A_c1]).
- Multi-step queries: First retrieve the data (via SQL or SEC RAG), then compute or synthesize your analysis.
- If a user asks a general conversational question or greeting that does not require financial data, answer directly without invoking tools.
- Never modify data or run unauthorized commands.
"""

class FinancialAgent:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model_name = settings.MODEL_NAME

    def run(self, user_query: str, conversation_history: list[dict[str, Any]] = None) -> ChatResponse:
        """
        Executes the Observe-Think-Act agentic loop with native tool calling and defense guardrails.
        """
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Append prior conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
            
        messages.append({"role": "user", "content": user_query})

        step_logs: list[ToolExecutionLog] = []
        collected_citations: list[Citation] = []
        seen_calls: set[str] = set()

        for step in range(settings.MAX_AGENT_STEPS):
            # 1. Model Call (Temperature 0 for deterministic evaluation)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.0
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # 2. If no tool is called, the agent has formulated its final answer
            if not tool_calls:
                return ChatResponse(
                    answer=response_message.content or "No response generated.",
                    steps=step_logs,
                    citations=collected_citations,
                    total_steps=step + 1
                )

            # 3. Process Tool Invocations
            # Append the assistant's tool-call intent to conversation context
            assistant_turn = {
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            }
            messages.append(assistant_turn)

            for tc in tool_calls:
                fn_name = tc.function.name
                fn_args_raw = tc.function.arguments
                
                # Check for infinite repeated calls
                call_fingerprint = f"{fn_name}:{fn_args_raw}"
                if call_fingerprint in seen_calls:
                    tool_output = {"success": False, "error": "Loop detected: exact tool call repeated."}
                else:
                    seen_calls.add(call_fingerprint)
                    try:
                        parsed_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                    except Exception as pe:
                        parsed_args = {"raw": fn_args_raw}

                    # Execute the tool
                    if fn_name in TOOL_MAP:
                        target_tool = TOOL_MAP[fn_name]
                        try:
                            tool_output = target_tool(**parsed_args)
                        except Exception as ex:
                            tool_output = {"success": False, "error": f"Tool execution failed: {str(ex)}"}
                    else:
                        tool_output = {"success": False, "error": f"Unknown tool: '{fn_name}'"}

                # Collect citations if SEC RAG returned any
                if fn_name == "sec_doc_rag" and isinstance(tool_output, dict):
                    for cit in tool_output.get("citations", []):
                        collected_citations.append(Citation(
                            source=cit.get("source", "SEC 10-K"),
                            snippet=cit.get("snippet", ""),
                            score=cit.get("relevance_score")
                        ))

                # Log step
                step_logs.append(ToolExecutionLog(
                    tool=fn_name,
                    args=parsed_args if isinstance(parsed_args, dict) else {},
                    output=tool_output,
                    error=tool_output.get("error") if isinstance(tool_output, dict) else None
                ))

                # Append tool result back to message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(tool_output, default=str)
                })

        # If loop exits without final response, synthesize a fallback
        return ChatResponse(
            answer="The agent reached the maximum step limit before finalizing an answer. Please review the intermediate step logs.",
            steps=step_logs,
            citations=collected_citations,
            total_steps=settings.MAX_AGENT_STEPS
        )
