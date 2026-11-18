from __future__ import annotations

from pathlib import Path

import duckdb


def connect(data_path: Path | str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(database=":memory:")
    con.execute("CREATE TABLE orders AS SELECT * FROM read_csv_auto(?)", [str(data_path)])
    return con


def total_revenue(con: duckdb.DuckDBPyConnection) -> float:
    return float(con.execute("SELECT COALESCE(SUM(revenue), 0) FROM orders").fetchone()[0])


def revenue_by(con, column: str) -> list[dict[str, object]]:
    q = f"SELECT {column} AS key, SUM(revenue) AS revenue FROM orders GROUP BY {column} ORDER BY revenue DESC"
    rows = con.execute(q).fetchall()
    return [{"key": r[0], "revenue": r[1]} for r in rows]


def top_n(con, n: int) -> list[dict[str, object]]:
    rows = con.execute(
        "SELECT product, SUM(revenue) AS revenue FROM orders GROUP BY product ORDER BY revenue DESC LIMIT ?",
        [n],
    ).fetchall()
    return [{"product": r[0], "revenue": r[1]} for r in rows]


def describe(con) -> dict[str, object]:
    count = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    cols = [r[0] for r in con.execute("DESCRIBE orders").fetchall()]
    return {"rows": count, "columns": cols}
