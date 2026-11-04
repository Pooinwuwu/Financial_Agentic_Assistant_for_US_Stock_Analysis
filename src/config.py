import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemma-4-E4B-it")
    
    # Storage paths
    DATA_DIR: Path = BASE_DIR / "data"
    SQLITE_DB_PATH: Path = DATA_DIR / "financials.db"
    SEC_INDEX_PATH: Path = DATA_DIR / "sec_chunks.json"
    
    # Target Stocks Portfolio
    TICKERS: list[str] = [
        "AAPL", "MSFT", "NVDA", "AMD", "GOOGL",
        "AMZN", "WMT", "META", "TSLA", "JPM"
    ]
    
    # Agent Guardrails
    MAX_AGENT_STEPS: int = 5
    SQL_ROW_LIMIT: int = 50
    CALC_TIMEOUT_SECONDS: int = 5

settings = Settings()
