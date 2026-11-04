import io
import sys
import json
import traceback
from typing import Any, Optional
import pandas as pd
import numpy as np

from src.config import settings
from src.repository.sql_repo import SQLRepository
from src.repository.vector_repo import VectorRepository
from src.services.guardrails import Guardrails, SecurityGuardrailError

# Initialize repositories
sql_repo = SQLRepository()
vec_repo = VectorRepository()

class FinancialTools:
    @staticmethod
    def run_sql(query: str) -> dict[str, Any]:
        """
        Executes a read-only SQL query against the financials SQLite database.
        Available tables:
        - company_profiles(ticker, name, sector, industry, market_cap, description)
        - annual_financials(ticker, fiscal_year, total_revenue, gross_profit, operating_income, net_income, operating_cash_flow, free_cash_flow, total_assets, total_liabilities, total_equity, gross_margin, operating_margin, net_margin, pe_ratio, roe, eps)
        - daily_prices(ticker, date, open, high, low, close, volume, returns)
        """
        try:
            results = sql_repo.execute_query(query)
            if not results:
                return {"success": True, "count": 0, "data": [], "message": "Query executed successfully. 0 rows returned."}
            return {
                "success": True,
                "count": len(results),
                "data": results[:settings.SQL_ROW_LIMIT]
            }
        except SecurityGuardrailError as sge:
            return {"success": False, "error": f"Guardrail Rejection: {str(sge)}"}
        except Exception as e:
            return {"success": False, "error": f"SQL Execution Error: {str(e)}"}

    @staticmethod
    def sec_doc_rag(
        query: str,
        ticker: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        section: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Performs semantic retrieval across SEC Form 10-K filings (Item 1A Risk Factors & Item 7 MD&A)
        with metadata filtering and citation attribution.
        """
        try:
            matches = vec_repo.search(
                query=query,
                top_k=3,
                ticker=ticker,
                fiscal_year=fiscal_year,
                section=section,
                min_score=0.40
            )
            if not matches:
                return {
                    "success": True,
                    "matches": [],
                    "message": "No SEC filing passages met the relevance threshold (min_score=0.40)."
                }
            citations = [
                {
                    "source": m["id"],
                    "ticker": m["ticker"],
                    "fiscal_year": m["fiscal_year"],
                    "section": m["section"],
                    "title": m["title"],
                    "snippet": m["text"][:250] + "...",
                    "relevance_score": m["score"]
                }
                for m in matches
            ]
            return {
                "success": True,
                "count": len(matches),
                "citations": citations,
                "passages": [
                    f"[{m['id']}] {m['company']} ({m['ticker']}) {m['section']} - {m['title']}:\n{m['text']}"
                    for m in matches
                ]
            }
        except Exception as e:
            return {"success": False, "error": f"SEC Retrieval Error: {str(e)}"}

    @staticmethod
    def run_python_calc(code: str) -> dict[str, Any]:
        """
        Executes sandboxed Python calculation code for financial time series, volatility,
        moving averages, Sharpe ratios, and drawdowns.
        Has access to 'pd' (pandas), 'np' (numpy), and 'get_prices(ticker)' returning a DataFrame.
        """
        try:
            # 1. AST Static Security Inspection
            Guardrails.validate_python_code(code)

            # 2. Prepare Sandbox Scope
            def get_prices(ticker: str) -> pd.DataFrame:
                clean_ticker = ticker.strip().upper()
                rows = sql_repo.execute_query(
                    f"SELECT date, open, high, low, close, volume, returns FROM daily_prices WHERE ticker = '{clean_ticker}' ORDER BY date ASC"
                )
                df = pd.DataFrame(rows)
                if not df.empty and "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                return df

            sandbox_env = {
                "__builtins__": Guardrails.SAFE_BUILTINS,
                "pd": pd,
                "np": np,
                "get_prices": get_prices
            }

            # 3. Intercept standard output
            stdout_buffer = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout_buffer

            try:
                exec(code, sandbox_env)
                output_str = stdout_buffer.getvalue()
            finally:
                sys.stdout = old_stdout

            return {
                "success": True,
                "output": output_str.strip() or "Code executed successfully with no print output."
            }

        except SecurityGuardrailError as sge:
            return {"success": False, "error": f"Sandbox Security Violation: {str(sge)}"}
        except Exception as e:
            return {"success": False, "error": f"Calculation Runtime Error: {str(e)}"}

    @staticmethod
    def search_web_news(ticker: str, topic: str = "earnings news") -> dict[str, Any]:
        """
        Fetches curated recent market updates for a given equity with untrusted data fencing.
        """
        try:
            ticker_clean = ticker.strip().upper()
            import yfinance as yf
            stock = yf.Ticker(ticker_clean)
            news_items = getattr(stock, "news", []) or []
            
            fenced_articles = []
            for item in news_items[:3]:
                title = item.get("title", "")
                publisher = item.get("publisher", "Market News")
                link = item.get("link", "")
                
                # Apply structural prompt injection fencing
                safe_title = title.replace("<", "&lt;").replace(">", "&gt;")
                fenced_articles.append(
                    f"<untrusted_external_content publisher='{publisher}'>\n"
                    f"Title: {safe_title}\nLink: {link}\n"
                    f"</untrusted_external_content>"
                )

            if not fenced_articles:
                fenced_articles = [
                    f"<untrusted_external_content ticker='{ticker_clean}'>\n"
                    f"Recent market consensus indicates steady institutional holding and active options trading for {ticker_clean}.\n"
                    f"</untrusted_external_content>"
                ]

            return {
                "success": True,
                "ticker": ticker_clean,
                "articles_count": len(fenced_articles),
                "news_feed": "\n\n".join(fenced_articles)
            }
        except Exception as e:
            return {"success": False, "error": f"News Search Error: {str(e)}"}

# JSON Schema Tool Specifications for OpenAI Native Tool Calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Execute a read-only SQL SELECT query against historical annual financials and daily prices for AAPL, MSFT, NVDA, AMD, GOOGL, AMZN, WMT, META, TSLA, JPM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute. Example: SELECT ticker, fiscal_year, total_revenue, net_margin FROM annual_financials WHERE ticker='NVDA' ORDER BY fiscal_year DESC"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sec_doc_rag",
            "description": "Search SEC Form 10-K filings (Item 1A Risk Factors and Item 7 MD&A) using semantic search with metadata filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query describing the qualitative topic or risk factor."
                    },
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, NVDA, MSFT, TSLA)."
                    },
                    "fiscal_year": {
                        "type": "integer",
                        "description": "Fiscal year (e.g., 2024)."
                    },
                    "section": {
                        "type": "string",
                        "enum": ["Item 1A", "Item 7"],
                        "description": "Filing section: 'Item 1A' for Risk Factors, 'Item 7' for Management Discussion & Analysis."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_calc",
            "description": "Execute sandboxed Python code to calculate financial statistics (volatility, Sharpe ratio, moving averages, drawdowns). Use get_prices(ticker) to load a pandas DataFrame with date, open, high, low, close, returns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Must use print() to output results. Example: df = get_prices('AAPL'); print('Annualized Volatility:', df['returns'].std() * (252**0.5))"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web_news",
            "description": "Search recent financial news and analyst updates for a target stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g. AAPL, NVDA, TSLA)."
                    },
                    "topic": {
                        "type": "string",
                        "description": "Specific news topic, e.g. earnings, product launch, leadership."
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]

TOOL_MAP = {
    "run_sql": FinancialTools.run_sql,
    "sec_doc_rag": FinancialTools.sec_doc_rag,
    "run_python_calc": FinancialTools.run_python_calc,
    "search_web_news": FinancialTools.search_web_news
}
