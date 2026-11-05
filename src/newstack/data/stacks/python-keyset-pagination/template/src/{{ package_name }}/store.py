"""SQLite storage and the one query shape that pages without skipping.

`fetch` is deliberately built from a whitelisted column name and a row-value
comparison, so the SQL is the same statement for every order and every page:
`WHERE (sort_key, id) > (?, ?) ORDER BY sort_key, id LIMIT size + 1`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import Cursor, InputError, Query

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    created_at INTEGER NOT NULL,
    title TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS items_created ON items (created_at, id);
CREATE INDEX IF NOT EXISTS items_title ON items (title, id);
"""

DEFAULT_SIZE = 20
MAX_SIZE = 500


class StoreError(RuntimeError):
    """The database is missing, locked, or not what this tool expects."""


@dataclass(frozen=True)
class Row:
    id: int
    created_at: int
    title: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "created_at": self.created_at, "title": self.title}


def _row(record: tuple[Any, ...]) -> Row:
    ident, created_at, title = record
    return Row(int(ident), int(created_at), str(title))


class Store:
    """One connection. A connection belongs to the thread that made it."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        try:
            self._db = sqlite3.connect(str(self.path), isolation_level=None)
        except sqlite3.Error as error:
            raise StoreError(f"cannot open {self.path}: {error}") from None
        self._db.row_factory = None
        self._db.execute("PRAGMA journal_mode = WAL")
        self._db.execute("PRAGMA synchronous = NORMAL")
        self._db.executescript(SCHEMA)

    # --- writing ---------------------------------------------------------

    def insert(self, ident: int, created_at: int, title: str) -> None:
        if isinstance(ident, bool) or not isinstance(ident, int):
            raise InputError(f"id must be an integer, got {ident!r}")
        if isinstance(created_at, bool) or not isinstance(created_at, int):
            raise InputError(f"created_at must be an integer, got {created_at!r}")
        if not isinstance(title, str) or not title:
            raise InputError("title must be a non-empty string")
        try:
            self._db.execute(
                "INSERT INTO items (id, created_at, title) VALUES (?, ?, ?)",
                (ident, created_at, title),
            )
        except sqlite3.Error as error:
            raise StoreError(f"cannot insert item {ident}: {error}") from None

    def delete(self, ident: int) -> None:
        self._db.execute("DELETE FROM items WHERE id = ?", (ident,))

    def seed(self, count: int, *, rng_seed: int = 7) -> list[int]:
        """Deterministic population with deliberate timestamp ties and shuffled ids."""
        import random

        if count < 1:
            raise InputError("seed needs at least one item")
        rng = random.Random(rng_seed)
        rows = [(index, 1_700_000_000 + index // 4, f"note {index:03d}") for index in range(count)]
        rng.shuffle(rows)
        for ident, created_at, title in rows:
            self.insert(ident, created_at, title)
        return [ident for ident, _, _ in rows]

    # --- reading ---------------------------------------------------------

    def _where(self, query: Query, cursor: Cursor | None, backwards: bool) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        arguments: list[Any] = []
        if query.title_prefix:
            clauses.append("title LIKE ?")
            arguments.append(f"{query.title_prefix}%")
        if cursor is not None:
            operator = "<" if query.order.descending else ">"
            if backwards:
                operator = ">" if query.order.descending else "<"
            clauses.append(f"({query.order.key}, id) {operator} (?, ?)")
            arguments.extend([cursor.sort_value, cursor.ident])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, arguments

    def fetch(
        self,
        query: Query | None = None,
        *,
        cursor: Cursor | None = None,
        size: int = DEFAULT_SIZE,
        backwards: bool = False,
    ) -> tuple[list[Row], bool]:
        """One page plus a flag saying whether anything lies beyond it."""
        spec = query or Query()
        if isinstance(size, bool) or not isinstance(size, int):
            raise InputError(f"size must be an integer, got {size!r}")
        if size < 1:
            raise InputError("size must be at least 1")
        if size > MAX_SIZE:
            raise InputError(f"size must be at most {MAX_SIZE}")
        if cursor is not None:
            cursor.check(spec)
        where, arguments = self._where(spec, cursor, backwards)
        order = spec.order.columns()
        if backwards:
            direction = "ASC" if spec.order.descending else "DESC"
            order = f"{spec.order.key} {direction}, id {direction}"
        sql = f"SELECT id, created_at, title FROM items {where} ORDER BY {order} LIMIT ?"
        try:
            rows = [_row(record) for record in self._db.execute(sql, [*arguments, size + 1])]
        except sqlite3.Error as error:
            raise StoreError(f"paging query failed: {error}") from None
        more = len(rows) > size
        rows = rows[:size]
        if backwards:
            rows.reverse()
        return rows, more

    def fetch_offset(
        self, query: Query | None = None, *, offset: int, size: int = DEFAULT_SIZE
    ) -> list[Row]:
        """The other way: LIMIT/OFFSET. Here so the demo can show what it costs."""
        spec = query or Query()
        if offset < 0:
            raise InputError("offset must not be negative")
        where, arguments = self._where(spec, None, False)
        sql = (
            f"SELECT id, created_at, title FROM items {where} "
            f"ORDER BY {spec.order.columns()} LIMIT ? OFFSET ?"
        )
        return [_row(record) for record in self._db.execute(sql, [*arguments, size, offset])]

    def count(self, query: Query | None = None) -> int:
        spec = query or Query()
        where, arguments = self._where(spec, None, False)
        sql = f"SELECT COUNT(*) FROM items {where}"
        return int(self._db.execute(sql, arguments).fetchone()[0])

    def ordered_ids(self, query: Query | None = None) -> list[int]:
        """Ground truth: the ids in the query's order, straight from the database."""
        spec = query or Query()
        where, arguments = self._where(spec, None, False)
        sql = f"SELECT id FROM items {where} ORDER BY {spec.order.columns()}"
        return [int(record[0]) for record in self._db.execute(sql, arguments)]

    def ids(self) -> list[int]:
        return [int(record[0]) for record in self._db.execute("SELECT id FROM items ORDER BY id")]

    def get(self, ident: int) -> Row | None:
        found = self._db.execute(
            "SELECT id, created_at, title FROM items WHERE id = ?", (ident,)
        ).fetchone()
        return None if found is None else _row(found)

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exception: object) -> None:
        self.close()
