"""A consumer that tolerates duplicates and refuses to reorder.

At-least-once delivery means the same event can arrive twice; the ledger makes
the second arrival free. Ordering is checked rather than assumed: an event whose
seq is not the next one is an error the consumer will not paper over.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .model import Event
from .store import StoreError, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries (
    consumer TEXT NOT NULL,
    event_id TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    PRIMARY KEY (consumer, event_id)
);
CREATE TABLE IF NOT EXISTS effects (
    consumer TEXT NOT NULL,
    aggregate TEXT NOT NULL,
    total INTEGER NOT NULL,
    last_seq INTEGER NOT NULL,
    PRIMARY KEY (consumer, aggregate)
);
"""


class ConsumerError(RuntimeError):
    """The stream is not the stream this consumer can apply."""


@dataclass
class Handled:
    applied: list[str]
    duplicates: list[str]

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    def line(self) -> str:
        return f"applied {self.applied_count}, duplicates {self.duplicate_count}"


class Consumer:
    """Deduplicates by event id and folds the payload into a per-aggregate total."""

    def __init__(self, path: Path | str, name: str, *, clock=now_iso) -> None:
        if not name:
            raise ConsumerError("consumer needs a name")
        self.name = name
        self.clock = clock
        try:
            self.conn = sqlite3.connect(str(path), isolation_level=None)
        except sqlite3.Error as error:
            raise StoreError(f"cannot open {path}: {error}") from error
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)

    def apply(self, event: Event) -> bool:
        """True when this event changed something, False when it was a repeat."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            cursor = self.conn.execute(
                "INSERT OR IGNORE INTO deliveries (consumer, event_id, applied_at) "
                "VALUES (?, ?, ?)",
                (self.name, event.event_id, self.clock()),
            )
            if cursor.rowcount == 0:
                self.conn.execute("COMMIT")
                return False
            row = self.conn.execute(
                "SELECT total, last_seq FROM effects WHERE consumer = ? AND aggregate = ?",
                (self.name, event.aggregate),
            ).fetchone()
            total = 0 if row is None else int(row["total"])
            last = 0 if row is None else int(row["last_seq"])
            if event.seq != last + 1:
                raise ConsumerError(
                    f"{event.aggregate}: got seq {event.seq} after {last}; "
                    "the relay reordered the stream"
                )
            amount = event.payload.get("amount", 0)
            self.conn.execute(
                "INSERT INTO effects (consumer, aggregate, total, last_seq) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (consumer, aggregate) DO UPDATE SET total = ?, last_seq = ?",
                (self.name, event.aggregate, total + int(amount), event.seq, total + int(amount),
                 event.seq),
            )
            self.conn.execute("COMMIT")
            return True
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    def handle(self, events: list[Event]) -> Handled:
        handled = Handled(applied=[], duplicates=[])
        for event in events:
            if self.apply(event):
                handled.applied.append(event.event_id)
            else:
                handled.duplicates.append(event.event_id)
        return handled

    def total(self, aggregate: str) -> int:
        row = self.conn.execute(
            "SELECT total FROM effects WHERE consumer = ? AND aggregate = ?",
            (self.name, aggregate),
        ).fetchone()
        return 0 if row is None else int(row["total"])

    def last_seq(self, aggregate: str) -> int:
        row = self.conn.execute(
            "SELECT last_seq FROM effects WHERE consumer = ? AND aggregate = ?",
            (self.name, aggregate),
        ).fetchone()
        return 0 if row is None else int(row["last_seq"])

    def applied_count(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM deliveries WHERE consumer = ?", (self.name,)
        ).fetchone()
        return int(row["n"])

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Consumer:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
