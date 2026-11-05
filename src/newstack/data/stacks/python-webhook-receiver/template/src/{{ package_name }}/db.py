"""SQLite ledger: one row per delivered event id, so a retry is not a second delivery."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent.parent / "migrations" / "001_events.sql"


def connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def migrate(connection: sqlite3.Connection) -> list[str]:
    """Apply every `*.sql` once. `executescript` commits before it runs, so the ledger
    insert has to travel inside the same explicit transaction."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    applied = {row["name"] for row in connection.execute("SELECT name FROM schema_migrations")}
    done = []
    for path in sorted(SCHEMA.parent.glob("*.sql")):
        if path.name in applied:
            continue
        body = path.read_text(encoding="utf-8")
        connection.executescript(
            "BEGIN;\n"
            + body
            + "\nINSERT INTO schema_migrations (name, applied_at) "
            + f"VALUES ('{path.name}', strftime('%Y-%m-%dT%H:%M:%fZ','now'));\n"
            + "COMMIT;\n"
        )
        done.append(path.name)
    return done
