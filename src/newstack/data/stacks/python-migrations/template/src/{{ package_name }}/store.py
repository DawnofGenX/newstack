"""The ledger: which migration ran, when, and what it hashed to.

The ledger lives in the database it describes, not in a file next to the
migrations. That is the only place where "this ran" and "these tables exist" are
updated by the same commit, so they cannot disagree after a crash.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from {{ package_name }}.migration import Migration

LEDGER = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    slug         TEXT NOT NULL,
    checksum     TEXT NOT NULL,
    applied_at   TEXT NOT NULL
)
"""


@dataclass(frozen=True)
class Applied:
    """A row of the ledger, as it was written."""

    migration_id: str
    slug: str
    checksum: str
    applied_at: str

    @property
    def label(self) -> str:
        """The filename without the extension."""
        return f"{self.migration_id}_{self.slug}"


def connect(path: str | Path) -> sqlite3.Connection:
    """Open the database with transactions under our control.

    ``isolation_level=None`` turns off the module's implicit transaction
    handling. That matters more than it looks: with the default setting the
    sqlite3 module never opens a transaction around DDL, so ``with connection:``
    gives you no rollback at all for ``CREATE TABLE`` — the statement is committed
    before the exception you were relying on happens. Every migration here opens
    its own transaction explicitly instead.
    """
    connection = sqlite3.connect(str(path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


class Store:
    """The migration ledger in an open database connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @classmethod
    def open(cls, path: str | Path) -> Store:
        """Open (or create) the database file and make sure the ledger exists."""
        return cls(connect(path))

    def ensure_ledger(self) -> None:
        """Create the ledger table if this is a fresh database."""
        self.connection.execute(LEDGER)

    def applied(self) -> dict[str, Applied]:
        """Every applied migration, keyed by id, in numeric order."""
        rows = self.connection.execute(
            "SELECT migration_id, slug, checksum, applied_at FROM schema_migrations"
        ).fetchall()
        found = {
            str(row["migration_id"]): Applied(
                migration_id=str(row["migration_id"]),
                slug=str(row["slug"]),
                checksum=str(row["checksum"]),
                applied_at=str(row["applied_at"]),
            )
            for row in rows
        }
        return {key: found[key] for key in sorted(found, key=int)}

    def close(self) -> None:
        """Close the connection this store was opened on."""
        self.connection.close()

    def record(self, migration: Migration, applied_at: str) -> None:
        """Write one ledger row. The caller owns the surrounding transaction."""
        self.connection.execute(
            "INSERT INTO schema_migrations (migration_id, slug, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (migration.migration_id, migration.slug, migration.checksum, applied_at),
        )
