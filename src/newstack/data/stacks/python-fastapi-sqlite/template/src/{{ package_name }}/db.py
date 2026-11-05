"""SQLite plumbing: one connection per request, migrations applied once."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"


def db_path() -> str:
    """Where the database lives; ``DB_PATH`` wins so tests can point elsewhere."""

    return os.environ.get("DB_PATH", "./notes.db")


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open the database with the pragmas every writer wants."""

    connection = sqlite3.connect(path or db_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    # WAL lets a reader work while a writer commits; both pragmas are per
    # connection, so every new connection sets them again.
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def applied_migrations(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT name FROM schema_migrations ORDER BY name").fetchall()
    return [row["name"] for row in rows]


def migrate(connection: sqlite3.Connection) -> list[str]:
    """Apply every ``migrations/*.sql`` file that has not run yet.

    Each file runs inside ONE transaction together with the row that records it,
    so a failing migration leaves the database exactly as it was. ``executescript``
    commits before it starts, so the transaction is opened inside the script
    instead of around it.
    """

    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " name TEXT PRIMARY KEY,"
        " applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
        ")"
    )
    connection.commit()
    done = set(applied_migrations(connection))
    ran: list[str] = []
    for path in sorted(SCHEMA_DIR.glob("*.sql")):
        if path.name in done:
            continue
        script = path.read_text()
        connection.executescript(
            "BEGIN;\n"
            f"{script}\n"
            "INSERT INTO schema_migrations (name) VALUES ("
            f"'{path.name}'"
            ");\n"
            "COMMIT;\n"
        )
        ran.append(path.name)
    return ran


def connection_scope() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: a connection that is always closed."""

    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
