"""Job rows: how a due job is claimed, run, and scheduled again."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

BACKOFF_BASE = 0.05
BACKOFF_CAP = 30.0
LEASE_SECONDS = 30.0
KINDS = ("count", "explode")


class JobError(ValueError):
    """A caller asked for something the scheduler will not do."""


def is_separator(byte: int) -> bool:
    return byte in (32, 9, 10, 13, 11, 12)


def count_text(text: str) -> dict[str, int]:
    raw = text.encode("utf-8")
    lines = 0
    words = 0
    inside = False
    for byte in raw:
        if byte == 10:
            lines += 1
        if is_separator(byte):
            inside = False
        elif not inside:
            inside = True
            words += 1
    return {"lines": lines, "words": words, "bytes": len(raw)}


def backoff(attempts: int) -> float:
    return min(BACKOFF_CAP, BACKOFF_BASE * (2 ** max(0, attempts - 1)))


def row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def create(
    connection: sqlite3.Connection,
    *,
    name: str,
    kind: str = "count",
    payload: str = "",
    run_at: float,
    interval_seconds: float | None = None,
    max_attempts: int = 3,
    at: float | None = None,
) -> dict[str, Any]:
    if not name.strip():
        raise JobError("name must not be blank")
    if kind not in KINDS:
        raise JobError(f"kind must be one of {', '.join(KINDS)}")
    if interval_seconds is not None and interval_seconds <= 0:
        raise JobError("interval_seconds must be positive")
    if max_attempts < 1:
        raise JobError("max_attempts must be at least 1")
    stamp = run_at if at is None else at
    job_id = uuid.uuid4().hex[:12]
    connection.execute(
        "INSERT INTO jobs (id, name, kind, payload, run_at, interval_seconds, status,"
        " attempts, max_attempts, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?)",
        (job_id, name.strip(), kind, payload, run_at, interval_seconds, max_attempts, stamp, stamp),
    )
    return fetch(connection, job_id)


def fetch(connection: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_job(row) if row is not None else None


def listing(connection: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        rows = connection.execute("SELECT * FROM jobs ORDER BY run_at, id").fetchall()
    else:
        rows = connection.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY run_at, id", (status,)
        ).fetchall()
    return [row_to_job(row) for row in rows]


def due_count(connection: sqlite3.Connection, at: float) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS n FROM jobs WHERE status = 'pending' AND run_at <= ?", (at,)
    ).fetchone()
    return int(row["n"])


def claim(
    connection: sqlite3.Connection, *, at: float, limit: int = 8, lease: float = LEASE_SECONDS
) -> list[dict[str, Any]]:
    """Take ownership of due jobs in one transaction.

    `BEGIN IMMEDIATE` is the whole trick: two tickers that only SELECT and then
    UPDATE would both read the same rows, and the second UPDATE would happily
    re-run a job the first one already took. The write lock makes the read and
    the update one step, so the second process sees the rows as gone.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        rows = connection.execute(
            "SELECT * FROM jobs WHERE status = 'pending' AND run_at <= ?"
            " AND (locked_until IS NULL OR locked_until <= ?)"
            " ORDER BY run_at, id LIMIT ?",
            (at, at, limit),
        ).fetchall()
        claimed: list[dict[str, Any]] = []
        for row in rows:
            connection.execute(
                "UPDATE jobs SET locked_until = ?, updated_at = ? WHERE id = ?",
                (at + lease, at, row["id"]),
            )
            job = row_to_job(row)
            job["locked_until"] = at + lease
            claimed.append(job)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    return claimed


def finish(
    connection: sqlite3.Connection,
    job: dict[str, Any],
    *,
    at: float,
    started_at: float | None = None,
    counts: dict[str, int] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Record the outcome and decide when (or whether) the job runs again."""
    ok = error is None
    attempts = job["attempts"] + (0 if ok else 1)
    interval = job["interval_seconds"]

    if ok:
        status = "pending" if interval else "done"
        # A one-shot job that ran is finished; an interval job is due again one
        # interval later. Adding whole elapsed intervals would make an overdue
        # job fire N times in a row to "catch up", which is never what a
        # scheduler wants.
        run_at = at + interval if interval else job["run_at"]
        last_error = None
    elif attempts >= job["max_attempts"]:
        status = "failed"
        run_at = job["run_at"]
        last_error = error
    else:
        status = "pending"
        run_at = at + backoff(attempts)
        last_error = error

    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "INSERT INTO runs (job_id, started_at, finished_at, status, lines, words, bytes, error)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job["id"],
                at if started_at is None else started_at,
                at,
                "ok" if ok else "error",
                (counts or {}).get("lines"),
                (counts or {}).get("words"),
                (counts or {}).get("bytes"),
                error,
            ),
        )
        connection.execute(
            "UPDATE jobs SET status = ?, attempts = ?, run_at = ?, locked_until = NULL,"
            " last_error = ?, updated_at = ? WHERE id = ?",
            (status, attempts, run_at, last_error, at, job["id"]),
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    return fetch(connection, job["id"]) or {}


def runs(connection: sqlite3.Connection, job_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM runs WHERE job_id = ? ORDER BY id", (job_id,)
    ).fetchall()
    return [row_to_job(row) for row in rows]


def execute(
    connection: sqlite3.Connection, job: dict[str, Any], *, at: float, started_at: float | None = None
) -> dict[str, Any]:
    """Run one job. The handler is not allowed to see the database."""
    try:
        if job["kind"] == "count":
            return finish(connection, job, at=at, started_at=started_at, counts=count_text(job["payload"]))
        raise RuntimeError("the explode job always fails")
    except Exception as exc:  # noqa: BLE001 - the scheduler records any failure
        return finish(
            connection, job, at=at, started_at=started_at, error=f"{type(exc).__name__}: {exc}"
        )
