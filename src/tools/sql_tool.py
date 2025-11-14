import sqlite3

import pandas as pd


def query_sqlite(db_path: str, sql: str) -> pd.DataFrame:
    """Executa SQL e retorna DataFrame."""
    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql, con)
        return df
    finally:
        con.close()
