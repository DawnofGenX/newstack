"""SQLite helpers for the worker."""

from __future__ import annotations

import os
import sqlite3


def db_path() -> str:
    return os.getenv("JOBS_DB", "jobs.db")


def connect() -> sqlite3.Connection:
    return sqlite3.connect(db_path())


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS job_runs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "tick INTEGER NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        conn.commit()


def reset_db() -> None:
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM job_runs")
        conn.commit()


def record_tick(tick: int) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO job_runs (tick) VALUES (?)", (tick,))
        conn.commit()


def count_runs() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM job_runs").fetchone()
    return int(row[0])