"""Storage: two tables, one file, and the rules that keep them honest."""

from __future__ import annotations

import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "migrations"
DEFAULT_DB = Path(os.environ.get("DB_PATH", "scheduler.db"))


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open a connection with the pragmas each connection has to set itself.

    `isolation_level=None` turns off the module's implicit transaction handling: a
    bare SELECT then takes no lock at all, which is why `claim()` has to ask for
    BEGIN IMMEDIATE explicitly.
    """
    target = Path(path) if path is not None else DEFAULT_DB
    connection = sqlite3.connect(str(target), check_same_thread=False, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def migrate(connection: sqlite3.Connection) -> list[str]:
    """Apply every unapplied migration, each one in its own transaction."""
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    applied = {row["name"] for row in connection.execute("SELECT name FROM schema_migrations")}
    done: list[str] = []
    for script in sorted(SCHEMA_DIR.glob("*.sql")):
        if script.name in applied:
            continue
        body = script.read_text(encoding="utf-8")
        # `executescript` commits whatever is pending *before* it runs, so the
        # BEGIN has to live inside the script text to make the pair atomic.
        connection.executescript(
            "BEGIN;\n"
            + body
            + "\nINSERT INTO schema_migrations (name, applied_at) VALUES ('"
            + script.name
            + "', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));\nCOMMIT;\n"
        )
        done.append(script.name)
    return done


@contextmanager
def connection_scope(path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()


def now() -> float:
    return time.time()
