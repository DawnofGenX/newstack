"""The append-only table: allocate a sequence number and a hash link under one write lock."""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Iterator, Sequence
from typing import Any

from .canon import canonical
from .record import GENESIS, Event, body_of, event_of, now_iso, stored_event

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq  INTEGER PRIMARY KEY,
    body TEXT NOT NULL,
    hash TEXT NOT NULL
);
"""


class StoreError(RuntimeError):
    """The log is not usable: a bad file, a busy database, or a forged row."""


class Store:
    """An audit log on disk. One connection, one thread, one writer at a time."""

    def __init__(self, path: Any, *, clock: Any = now_iso, busy_timeout_s: float = 5.0) -> None:
        self.path = path
        self.clock = clock
        try:
            self._conn = sqlite3.connect(str(path), timeout=busy_timeout_s, isolation_level=None)
        except sqlite3.Error as error:
            raise StoreError(f"cannot open {path}: {error}") from error
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_s * 1000)}")
        self._conn.executescript(SCHEMA)

    @contextlib.contextmanager
    def _transaction(self) -> Iterator[None]:
        # IMMEDIATE takes the write lock before the read that picks `seq`, so two writers cannot
        # both see the same head and mint the same sequence number.
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    def append(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        detail: dict[str, Any] | None = None,
        at: str | None = None,
    ) -> Event:
        """Append one event and return it with its hash."""
        stamp = at if at is not None else self.clock()
        try:
            with self._transaction():
                head = self._head()
                seq = 1 if head is None else head.seq + 1
                previous = GENESIS if head is None else head.hash
                body = body_of(
                    seq, actor, action, target, detail=detail, prev_hash=previous, at=stamp
                )
                event = event_of(body)
                self._conn.execute(
                    "INSERT INTO events (seq, body, hash) VALUES (?, ?, ?)",
                    (seq, canonical(body), event.hash),
                )
        except sqlite3.Error as error:
            raise StoreError(f"cannot append to {self.path}: {error}") from error
        return event

    def _head(self) -> Event | None:
        row = self._conn.execute(
            "SELECT seq, body, hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return None if row is None else stored_event(row["body"], row["hash"])

    def head(self) -> Event | None:
        return self._head()

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS total FROM events").fetchone()
        return int(row["total"])

    def events(self, start: int = 1, limit: int | None = None) -> list[Event]:
        """Ordered by `seq`, because the timestamps are not ordered (clocks go backwards)."""
        sql = "SELECT seq, body, hash FROM events WHERE seq >= ? ORDER BY seq"
        params: list[Any] = [start]
        if limit is not None:
            if limit < 1:
                raise ValueError(f"limit must be at least 1, got {limit}")
            sql += " LIMIT ?"
            params.append(limit)
        return [stored_event(row["body"], row["hash"]) for row in self._conn.execute(sql, params)]

    def get(self, seq: int) -> Event | None:
        row = self._conn.execute(
            "SELECT seq, body, hash FROM events WHERE seq = ?", (seq,)
        ).fetchone()
        return None if row is None else stored_event(row["body"], row["hash"])

    def sequence(self) -> Sequence[int]:
        rows = self._conn.execute("SELECT seq FROM events ORDER BY seq")
        return [row["seq"] for row in rows]

    def raw(self) -> sqlite3.Connection:
        """The connection, for forensic tooling and for the demo's attacker. Not for app code."""
        return self._conn

    def close(self) -> None:
        with contextlib.suppress(sqlite3.Error):
            self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
