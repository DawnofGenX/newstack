"""SQLite, with the outbox table in the same database as the business rows.

Being in the same database is the whole trick: one `BEGIN IMMEDIATE` covers the
insert into `orders` and the insert into `outbox`, so a crash either loses both
or neither.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .model import Event, InputError, Order, payload_text

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    position INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    aggregate TEXT NOT NULL,
    seq INTEGER NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT,
    UNIQUE (aggregate, seq)
);
CREATE INDEX IF NOT EXISTS outbox_pending ON outbox (position) WHERE published_at IS NULL;
"""


class StoreError(RuntimeError):
    """The database could not be opened or written."""


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


class Store:
    def __init__(self, path: Path | str, *, clock=now_iso, busy_timeout_s: float = 5.0) -> None:
        self.path = Path(path)
        self.clock = clock
        try:
            self.conn = sqlite3.connect(
                str(self.path), timeout=busy_timeout_s, isolation_level=None
            )
        except sqlite3.Error as error:
            raise StoreError(f"cannot open {self.path}: {error}") from error
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_s * 1000)}")
        self.conn.executescript(SCHEMA)

    # --- plumbing -----------------------------------------------------------
    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """BEGIN IMMEDIATE takes the write lock before the first read.

        A deferred transaction reads first and decides to write second, which is
        how two writers both read seq 1 and one of them loses on the unique
        index. The lock is per database file, so it costs nothing on one writer.
        """
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        self.conn.execute("COMMIT")

    def _append(
        self, aggregate: str, kind: str, payload: dict[str, Any], *, seq: int | None = None
    ) -> Event:
        text = payload_text(payload)
        if seq is None:
            row = self.conn.execute(
                "SELECT COALESCE(MAX(seq), 0) AS last FROM outbox WHERE aggregate = ?",
                (aggregate,),
            ).fetchone()
            seq = int(row["last"]) + 1
        event = Event(
            event_id=uuid.uuid4().hex,
            aggregate=aggregate,
            seq=seq,
            kind=kind,
            payload=payload,
            created_at=self.clock(),
        )
        cursor = self.conn.execute(
            "INSERT INTO outbox (event_id, aggregate, seq, kind, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (event.event_id, aggregate, seq, kind, text, event.created_at),
        )
        return Event(
            event_id=event.event_id,
            aggregate=aggregate,
            seq=seq,
            kind=kind,
            payload=payload,
            created_at=event.created_at,
            position=int(cursor.lastrowid or 0),
        )

    # --- the safe path ------------------------------------------------------
    def place_order(self, amount: int, *, kind: str = "order.placed") -> tuple[Order, Event]:
        """Write the order and its event in one transaction.

        There is no moment here at which the row exists without the event.
        """
        self._check_amount(amount)
        with self._transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO orders (amount, status) VALUES (?, 'placed')", (amount,)
            )
            ident = int(cursor.lastrowid or 0)
            event = self._append(f"order:{ident}", kind, {"amount": amount, "order": ident})
        return Order(ident=ident, amount=amount, status="placed"), event

    def pay_order(self, ident: int) -> Event:
        order = self.order(ident)
        if order.status == "paid":
            raise InputError(f"order {ident} was already paid")
        with self._transaction() as conn:
            conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (ident,))
            return self._append(f"order:{ident}", "order.paid", {"order": ident})

    def place_order_unsafe(self, amount: int) -> Order:
        """Two transactions — the shape that loses events.

        The order commits on its own, and the event is written afterwards by a
        caller that might never get there. The demo uses this to show the loss
        an outbox is supposed to make impossible.
        """
        self._check_amount(amount)
        with self._transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO orders (amount, status) VALUES (?, 'placed')", (amount,)
            )
            ident = int(cursor.lastrowid or 0)
        return Order(ident=ident, amount=amount, status="placed")

    def record_event(self, aggregate: str, kind: str, payload: dict[str, Any]) -> Event:
        with self._transaction():
            return self._append(aggregate, kind, payload)

    @staticmethod
    def _check_amount(amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise InputError(f"amount must be an integer, got {type(amount).__name__}")
        if amount <= 0:
            raise InputError(f"amount must be positive, got {amount}")

    # --- reads --------------------------------------------------------------
    def unpublished(self, *, limit: int = 50) -> list[Event]:
        """In outbox order, which is the order the writes happened in."""
        if limit < 1:
            raise InputError(f"limit must be at least 1, got {limit}")
        rows = self.conn.execute(
            "SELECT * FROM outbox WHERE published_at IS NULL ORDER BY position LIMIT ?",
            (limit,),
        ).fetchall()
        return [_event(row) for row in rows]

    def events(
        self, *, aggregate: str | None = None, pending_only: bool = False, limit: int | None = None
    ) -> list[Event]:
        sql = "SELECT * FROM outbox"
        clauses: list[str] = []
        values: list[object] = []
        if aggregate is not None:
            clauses.append("aggregate = ?")
            values.append(aggregate)
        if pending_only:
            clauses.append("published_at IS NULL")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY position"
        if limit is not None:
            sql += " LIMIT ?"
            values.append(limit)
        return [_event(row) for row in self.conn.execute(sql, values).fetchall()]

    def mark_published(self, event_id: str) -> bool:
        with self._transaction():
            cursor = self.conn.execute(
                "UPDATE outbox SET published_at = ? WHERE event_id = ? AND published_at IS NULL",
                (self.clock(), event_id),
            )
            return cursor.rowcount == 1

    def get(self, event_id: str) -> Event:
        row = self.conn.execute("SELECT * FROM outbox WHERE event_id = ?", (event_id,)).fetchone()
        if row is None:
            raise StoreError(f"no event {event_id!r}")
        return _event(row)

    def order(self, ident: int) -> Order:
        row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (ident,)).fetchone()
        if row is None:
            raise StoreError(f"no order {ident}")
        return Order(ident=int(row["id"]), amount=int(row["amount"]), status=str(row["status"]))

    def orders(self) -> list[Order]:
        rows = self.conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
        return [
            Order(ident=int(row["id"]), amount=int(row["amount"]), status=str(row["status"]))
            for row in rows
        ]

    def pending_count(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM outbox WHERE published_at IS NULL"
        ).fetchone()
        return int(row["n"])

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS n FROM outbox").fetchone()["n"])

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _event(row: sqlite3.Row) -> Event:
    return Event(
        event_id=str(row["event_id"]),
        aggregate=str(row["aggregate"]),
        seq=int(row["seq"]),
        kind=str(row["kind"]),
        payload=json.loads(row["payload"]),
        created_at=str(row["created_at"]),
        position=int(row["position"]),
        published_at=None if row["published_at"] is None else str(row["published_at"]),
    )
