"""The key table: claim it before the effect, complete it after."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from . import model

SCHEMA = """
CREATE TABLE IF NOT EXISTS idempotency (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    state TEXT NOT NULL,
    status INTEGER,
    body TEXT,
    claimed_at REAL NOT NULL,
    completed_at REAL,
    lease_until REAL NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (scope, key)
);
CREATE INDEX IF NOT EXISTS idempotency_age ON idempotency (state, completed_at);
"""

DEFAULT_LEASE_S = 30.0


class StoreError(RuntimeError):
    """The database could not do what was asked."""


@dataclass(frozen=True)
class Claim:
    """The right to run the handler once, or the answer already on file."""

    attempt: int
    replay: bool
    status: int | None = None
    body: str | None = None

    @property
    def fresh(self) -> bool:
        return not self.replay


class Store:
    """One connection, one thread. A second worker opens a second Store."""

    def __init__(
        self,
        path: str | Path,
        *,
        clock=time.time,
        lease_s: float = DEFAULT_LEASE_S,
        busy_timeout_s: float = 5.0,
    ) -> None:
        if lease_s <= 0:
            raise ValueError(f"lease_s must be positive, got {lease_s!r}")
        self.path = Path(path)
        self.clock = clock
        self.lease_s = lease_s
        try:
            self._conn = sqlite3.connect(
                str(self.path), timeout=busy_timeout_s, isolation_level=None
            )
        except sqlite3.Error as error:
            raise StoreError(f"cannot open {self.path}: {error}") from error
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_s * 1000)}")
        self._enable_wal()
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.executescript(SCHEMA)

    def _enable_wal(self, attempts: int = 20) -> None:
        """busy_timeout does not cover the journal_mode switch, so retry it here."""
        for attempt in range(attempts):
            try:
                self._conn.execute("PRAGMA journal_mode = WAL")
                return
            except sqlite3.OperationalError as error:
                if "locked" not in str(error) or attempt == attempts - 1:
                    raise StoreError(f"cannot enable WAL on {self.path}: {error}") from error
                time.sleep(0.02)

    def claim(self, request: model.Request, *, lease_s: float | None = None) -> Claim:
        """Take the key, replay it, or refuse. Always a short transaction."""
        lease = self.lease_s if lease_s is None else lease_s
        now = self.clock()
        with self._transaction():
            row = self._row(request)
            if row is None:
                self._conn.execute(
                    "INSERT INTO idempotency"
                    " (scope, key, fingerprint, state, claimed_at, lease_until, attempts)"
                    " VALUES (?, ?, ?, 'claimed', ?, ?, 1)",
                    (request.scope, request.key, request.fingerprint, now, now + lease),
                )
                return Claim(attempt=1, replay=False)
            if row["fingerprint"] != request.fingerprint:
                raise model.Mismatch(request.key, row["fingerprint"], request.fingerprint)
            if row["state"] == "completed":
                return Claim(
                    attempt=row["attempts"], replay=True, status=row["status"], body=row["body"]
                )
            if row["lease_until"] > now:
                raise model.InProgress(request.key, row["lease_until"] - now)
            attempt = row["attempts"] + 1
            self._conn.execute(
                "UPDATE idempotency SET claimed_at = ?, lease_until = ?, attempts = ?"
                " WHERE scope = ? AND key = ?",
                (now, now + lease, attempt, request.scope, request.key),
            )
            return Claim(attempt=attempt, replay=False)

    def complete(
        self, request: model.Request, attempt: int, response: model.Response
    ) -> None:
        """Store the answer, but only if this attempt still owns the row."""
        now = self.clock()
        with self._transaction():
            changed = self._conn.execute(
                "UPDATE idempotency SET state = 'completed', status = ?, body = ?,"
                " completed_at = ?, lease_until = ?"
                " WHERE scope = ? AND key = ? AND attempts = ? AND state = 'claimed'",
                (
                    response.status,
                    response.body,
                    now,
                    now,
                    request.scope,
                    request.key,
                    attempt,
                ),
            ).rowcount
            if changed != 1:
                raise model.OwnerLost(request.key, attempt)

    def release(self, request: model.Request, attempt: int) -> None:
        """Give the key back after a failure, so a retry need not wait for the lease."""
        with self._transaction():
            changed = self._conn.execute(
                "UPDATE idempotency SET lease_until = 0"
                " WHERE scope = ? AND key = ? AND attempts = ? AND state = 'claimed'",
                (request.scope, request.key, attempt),
            ).rowcount
            if changed != 1:
                raise model.OwnerLost(request.key, attempt)

    def get(self, scope: str, key: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM idempotency WHERE scope = ? AND key = ?", (scope, key)
        ).fetchone()

    def count(self, state: str | None = None) -> int:
        if state is not None and state not in model.STATES:
            raise ValueError(f"unknown state {state!r}; expected one of {', '.join(model.STATES)}")
        if state is None:
            row = self._conn.execute("SELECT COUNT(*) FROM idempotency").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM idempotency WHERE state = ?", (state,)
            ).fetchone()
        return int(row[0])

    def prune(self, older_than_s: float) -> int:
        """Forget completed keys older than the window. Live claims are never pruned."""
        if older_than_s < 0:
            raise ValueError(f"older_than_s must not be negative, got {older_than_s!r}")
        cutoff = self.clock() - older_than_s
        with self._transaction():
            return self._conn.execute(
                "DELETE FROM idempotency WHERE state = 'completed' AND completed_at <= ?",
                (cutoff,),
            ).rowcount

    def _row(self, request: model.Request) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM idempotency WHERE scope = ? AND key = ?",
            (request.scope, request.key),
        ).fetchone()

    def _transaction(self):
        return _Transaction(self._conn)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exception: object) -> None:
        self.close()


class _Transaction:
    """BEGIN IMMEDIATE, because a deferred transaction reads first and forks."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self) -> None:
        self._conn.execute("BEGIN IMMEDIATE")

    def __exit__(self, kind: object, value: object, traceback: object) -> None:
        if kind is None:
            self._conn.execute("COMMIT")
        else:
            self._conn.execute("ROLLBACK")
