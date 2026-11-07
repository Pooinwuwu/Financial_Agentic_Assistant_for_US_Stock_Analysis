# 1 import module and connection
import sqlite3
import pathlib

db_path = pathlib.Path("data/stocks.db")
db_path.parent.mkdir(parents=True, exist_ok=True)