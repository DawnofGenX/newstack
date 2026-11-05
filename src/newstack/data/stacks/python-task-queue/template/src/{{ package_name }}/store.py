"""A SQLite-backed job queue whose delivery guarantee is written down and tested.

The guarantee is *at least once*: a job is handed to a worker with a lease, and if
the worker dies the lease expires and the job is handed out again. That means the
same job can run twice, so the only sane contract is an idempotent handler — and
the only way to keep that contract is to make "I have the lease" checkable, which
is what ``complete`` and ``heartbeat`` do.

One :class:`Store` per thread. A SQLite connection is not shareable across
threads, so the concurrency test builds one store per worker.

Claiming is a single statement. A ``SELECT`` followed by an ``UPDATE`` lets two
workers read the same row and both believe they own it; the ``UPDATE ... WHERE
id = (SELECT ...)`` form makes the row lock part of the statement, and
``RETURNING`` hands back what was actually won.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

READY = "ready"
LEASED = "leased"
DONE = "done"
DEAD = "dead"
STATES = (READY, LEASED, DONE, DEAD)

DEFAULT_QUEUE = "default"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_LEASE_S = 30.0
DEFAULT_BACKOFF_BASE_S = 1.0
DEFAULT_BACKOFF_CAP_S = 60.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id           TEXT PRIMARY KEY,
    queue        TEXT NOT NULL,
    payload      TEXT NOT NULL,
    state        TEXT NOT NULL,
    attempts     INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL,
    created_at   REAL NOT NULL,
    available_at REAL NOT NULL,
    lease_until  REAL,
    worker       TEXT,
    last_error   TEXT,
    result       TEXT,
    finished_at  REAL
);
CREATE INDEX IF NOT EXISTS jobs_claimable ON jobs (state, available_at);
"""


class QueueError(Exception):
    """The queue was asked to do something it refuses to pretend to do."""


class LeaseLost(QueueError):
    """The lease expired or was taken: whatever this worker produced is not authoritative."""


@dataclass(frozen=True)
class Job:
    id: str
    queue: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int


class Store:
    def __init__(
        self,
        path: Path | str,
        *,
        clock: Callable[[], float] = time.time,
        backoff_base_s: float = DEFAULT_BACKOFF_BASE_S,
        backoff_cap_s: float = DEFAULT_BACKOFF_CAP_S,
        busy_timeout_s: float = 5.0,
    ) -> None:
        self.path = Path(path)
        self.clock = clock
        self.backoff_base_s = backoff_base_s
        self.backoff_cap_s = backoff_cap_s
        # WAL lets a reader run while a writer holds the lock, and busy_timeout turns
        # "database is locked" into a wait instead of a crash under load.
        self.connection = sqlite3.connect(
            self.path, timeout=busy_timeout_s, isolation_level=None, check_same_thread=True
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute(f"PRAGMA busy_timeout={int(busy_timeout_s * 1000)}")
        self.connection.executescript(SCHEMA)

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- writing -----------------------------------------------------------
    def push(
        self,
        payload: dict[str, Any],
        *,
        queue: str = DEFAULT_QUEUE,
        delay_s: float = 0.0,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> str:
        if not isinstance(payload, dict):
            raise QueueError(f"payload must be an object, got {type(payload).__name__}")
        if max_attempts < 1:
            raise QueueError("max_attempts must be at least 1")
        if delay_s < 0:
            raise QueueError("delay_s cannot be negative")
        text = _encode(payload)
        now = self.clock()
        job_id = uuid.uuid4().hex
        self.connection.execute(
            "INSERT INTO jobs (id, queue, payload, state, attempts, max_attempts,"
            " created_at, available_at) VALUES (?, ?, ?, ?, 0, ?, ?, ?)",
            (job_id, queue, text, READY, max_attempts, now, now + delay_s),
        )
        return job_id

    # -- claiming ----------------------------------------------------------
    def claim(
        self, worker: str, *, lease_s: float = DEFAULT_LEASE_S, queue: str | None = None
    ) -> Job | None:
        if lease_s <= 0:
            raise QueueError("lease_s must be positive")
        now = self.clock()
        self.reap()
        sql = """
            UPDATE jobs
               SET state = ?, worker = ?, lease_until = ?, attempts = attempts + 1
             WHERE id = (
                   SELECT id FROM jobs
                    WHERE attempts < max_attempts
                      AND available_at <= ?
                      AND (state = ? OR (state = ? AND lease_until <= ?))
                    {queue_filter}
                    ORDER BY available_at, created_at, id
                    LIMIT 1)
            RETURNING id, queue, payload, attempts, max_attempts
        """.format(queue_filter="AND queue = ?" if queue is not None else "")
        parameters: list[Any] = [LEASED, worker, now + lease_s, now, READY, LEASED, now]
        if queue is not None:
            parameters.append(queue)
        row = self.connection.execute(sql, parameters).fetchone()
        if row is None:
            return None
        return Job(
            id=row["id"],
            queue=row["queue"],
            payload=_decode(row["payload"]),
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
        )

    def reap(self) -> int:
        """A lease that outlived its last attempt is dead, not retryable."""
        now = self.clock()
        cursor = self.connection.execute(
            "UPDATE jobs SET state = ?, worker = NULL, lease_until = NULL,"
            " last_error = COALESCE(last_error, 'lease expired on the final attempt')"
            " WHERE state = ? AND lease_until <= ? AND attempts >= max_attempts",
            (DEAD, LEASED, now),
        )
        return cursor.rowcount

    # -- finishing ---------------------------------------------------------
    def heartbeat(self, job: Job, worker: str, *, lease_s: float = DEFAULT_LEASE_S) -> None:
        cursor = self.connection.execute(
            "UPDATE jobs SET lease_until = ? WHERE id = ? AND worker = ? AND state = ?",
            (self.clock() + lease_s, job.id, worker, LEASED),
        )
        if cursor.rowcount != 1:
            raise LeaseLost(f"job {job.id} is no longer leased by {worker}")

    def complete(self, job: Job, worker: str, result: Any = None) -> None:
        text = None if result is None else _encode({"result": result})
        cursor = self.connection.execute(
            "UPDATE jobs SET state = ?, worker = NULL, lease_until = NULL, result = ?,"
            " finished_at = ? WHERE id = ? AND worker = ? AND state = ?",
            (DONE, text, self.clock(), job.id, worker, LEASED),
        )
        if cursor.rowcount != 1:
            raise LeaseLost(
                f"job {job.id} was not completed: the lease had already expired and "
                "another worker owns it now"
            )

    def fail(self, job: Job, worker: str, error: str) -> str:
        row = self.connection.execute(
            "SELECT state, worker, attempts, max_attempts FROM jobs WHERE id = ?", (job.id,)
        ).fetchone()
        if row is None:
            raise QueueError(f"no such job {job.id}")
        if row["state"] != LEASED or row["worker"] != worker:
            raise LeaseLost(f"job {job.id} is no longer leased by {worker}")
        if row["attempts"] >= row["max_attempts"]:
            state = DEAD
            available_at = self.clock()
        else:
            state = READY
            available_at = self.clock() + self.backoff_for(row["attempts"])
        self.connection.execute(
            "UPDATE jobs SET state = ?, worker = NULL, lease_until = NULL, last_error = ?,"
            " available_at = ? WHERE id = ?",
            (state, error, available_at, job.id),
        )
        return state

    def backoff_for(self, attempts: int) -> float:
        """Exponential, capped. Attempt 1 waits the base, 2 waits twice that, and so on."""
        return min(self.backoff_cap_s, self.backoff_base_s * 2 ** (attempts - 1))

    # -- reading -----------------------------------------------------------
    def get(self, job_id: str) -> dict[str, Any]:
        row = self.connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise QueueError(f"no such job {job_id}")
        return _row(row)

    def list(self, *, state: str | None = None, queue: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM jobs"
        clauses: list[str] = []
        parameters: list[Any] = []
        if state is not None:
            if state not in STATES:
                raise QueueError(f"unknown state {state!r}; expected one of {', '.join(STATES)}")
            clauses.append("state = ?")
            parameters.append(state)
        if queue is not None:
            clauses.append("queue = ?")
            parameters.append(queue)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at, id"
        return [_row(row) for row in self.connection.execute(sql, parameters)]

    def stats(self) -> dict[str, int]:
        counts = dict.fromkeys(STATES, 0)
        for row in self.connection.execute("SELECT state, COUNT(*) AS n FROM jobs GROUP BY state"):
            counts[row["state"]] = row["n"]
        return counts

    def ready_count(self, *, queue: str | None = None) -> int:
        if queue is None:
            row = self.connection.execute(
                "SELECT COUNT(*) AS n FROM jobs WHERE state = ? AND available_at <= ?",
                (READY, self.clock()),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT COUNT(*) AS n FROM jobs WHERE state = ? AND available_at <= ?"
                " AND queue = ?",
                (READY, self.clock(), queue),
            ).fetchone()
        return int(row["n"])


def _encode(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    except TypeError as error:
        raise QueueError(f"payload is not JSON-serialisable: {error}") from error


def _decode(text: str) -> dict[str, Any]:
    return json.loads(text)


def _row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["payload"] = _decode(data["payload"])
    if data["result"] is not None:
        data["result"] = _decode(data["result"])
    return data
