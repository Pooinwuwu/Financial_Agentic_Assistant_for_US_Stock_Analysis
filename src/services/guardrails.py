import re
import ast
from typing import Any, Tuple

class SecurityGuardrailError(Exception):
    """Custom exception raised when a security guardrail boundary is violated."""
    pass

class Guardrails:
    # Denied SQL keywords and tokens that modify state or compromise isolation
    SQL_DISALLOWED_PATTERNS = [
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE)\b",
        r"\b(PRAGMA|ATTACH|DETACH|VACUUM|REINDEX)\b",
        r"\b(EXEC|EXECUTE|SYSTEM)\b",
        r";",           # Reject multi-statement queries
        r"--",          # Reject SQL inline comment tricks
        r"/\*",         # Reject SQL block comments
    ]
    
    # Safe builtins allowed in Python calculation sandbox
    SAFE_BUILTINS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "print": print,
    }

    # Modules blocked in Python calculation sandbox
    DISALLOWED_MODULES = {
        "os", "sys", "subprocess", "shutil", "socket", "http", "urllib",
        "requests", "pathlib", "importlib", "pickle", "builtins", "io"
    }

    @classmethod
    def validate_sql(cls, sql_query: str, default_limit: int = 50) -> str:
        """
        Validates that a SQL query is strictly a read-only SELECT statement,
        free of multi-statement injection and malicious syntax, and injects a LIMIT clause if absent.
        """
        stripped = sql_query.strip()
        if not stripped:
            raise SecurityGuardrailError("Empty SQL query rejected.")
        
        # Check against disallowed patterns (case-insensitive)
        for pattern in cls.SQL_DISALLOWED_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                raise SecurityGuardrailError(f"Security Guardrail: Disallowed SQL pattern detected: '{pattern}'.")
        
        # Must start with SELECT or WITH (for CTEs)
        if not (stripped.upper().startswith("SELECT") or stripped.upper().startswith("WITH")):
            raise SecurityGuardrailError("Security Guardrail: Only SELECT or WITH queries are permitted.")
        
        # Check for LIMIT clause, append if missing
        if not re.search(r"\bLIMIT\s+\d+\b", stripped, re.IGNORECASE):
            stripped = f"{stripped} LIMIT {default_limit}"
            
        return stripped

    @classmethod
    def validate_python_code(cls, code_str: str) -> None:
        """
        Parses AST of the Python script to block forbidden imports, function calls, and attribute access.
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            raise SecurityGuardrailError(f"Syntax error in calculation script: {e}")

        for node in ast.walk(tree):
            # Block forbidden imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in cls.DISALLOWED_MODULES:
                        raise SecurityGuardrailError(f"Security Guardrail: Module '{root_pkg}' is blocked in sandbox.")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in cls.DISALLOWED_MODULES:
                        raise SecurityGuardrailError(f"Security Guardrail: Module '{root_pkg}' is blocked in sandbox.")
            
            # Block builtins abuse like __import__, eval, exec, open
            elif isinstance(node, ast.Name):
                if node.id in {"eval", "exec", "open", "__import__", "compile", "globals", "locals"}:
                    raise SecurityGuardrailError(f"Security Guardrail: Builtin function '{node.id}' is forbidden.")
            
            # Block dunder attribute access like __class__, __subclasses__
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    raise SecurityGuardrailError(f"Security Guardrail: Access to dunder attribute '{node.attr}' is forbidden.")

    @classmethod
    def check_loop_budget(cls, current_step: int, max_steps: int) -> None:
        """
        Guards against infinite agent loops by enforcing maximum iterations.
        """
        if current_step >= max_steps:
            raise SecurityGuardrailError(f"Security Guardrail: Execution halted. Exceeded maximum step limit ({max_steps}).")
