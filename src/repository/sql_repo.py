import sqlite3
from typing import Any
from src.config import settings
from src.services.guardrails import Guardrails, SecurityGuardrailError

class SQLRepository:
    def __init__(self, db_path: str = None):
        self.db_path = str(db_path or settings.SQLITE_DB_PATH)

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        """
        Validates the SQL query against safety guardrails, enforces read-only connection,
        and returns query results as a list of dictionaries.
        """
        # Enforce guardrails (SELECT only, no comments, no semicolons, limit appended)
        guarded_query = Guardrails.validate_sql(query, default_limit=settings.SQL_ROW_LIMIT)

        # Open SQLite in URI read-only mode to prevent any filesystem writes
        uri = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(guarded_query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_table_schema(self) -> str:
        """Returns the DDL schemas of available tables for LLM prompt context."""
        uri = f"file:{self.db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall() if row[0]]
            return "\n\n".join(tables)
        finally:
            conn.close()
