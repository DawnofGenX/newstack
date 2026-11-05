"""An append-only record of what the saga did, in the order it did it.

The journal is the source of truth. A saga is not "run once and remembered in
RAM": if the process dies between charging a card and booking a flight, the
next process has to know that the charge happened, which is exactly what this
file answers. Every line is one JSON object, appended with ``O_APPEND`` and
fsynced, so a crash can lose the tail of a line but never rewrite history.

A torn final line is the one failure mode we can read past: the writer died
mid-append, so the effect it was about to record may or may not have happened.
Dropping that line is honest only because the runner re-executes an interrupted
step with the same idempotency key. A torn line in the *middle* is a different
thing -- somebody edited or truncated the file -- and it raises instead of
quietly shifting every later record up by one.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EVENTS = (
    "saga.started",
    "saga.completed",
    "saga.rolled_back",
    "saga.incomplete",
    "step.started",
    "step.retried",
    "step.succeeded",
    "step.failed",
    "step.compensated",
    "step.compensation_failed",
    "step.unrecoverable",
)

STEP_SUCCEEDED = "step.succeeded"
STEP_FAILED = "step.failed"
STEP_COMPENSATED = "step.compensated"
STEP_COMPENSATION_FAILED = "step.compensation_failed"


class JournalError(RuntimeError):
    """The journal cannot be read or written without guessing."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def read(path: str | Path) -> list[dict[str, Any]]:
    """Read every record, tolerating only a torn *final* line."""
    file = Path(path)
    if not file.exists():
        return []
    text = file.read_text(encoding="utf-8")
    if not text:
        return []
    lines = text.splitlines()
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            if number == len(lines):
                continue  # the writer died mid-append; the runner re-runs the step
            raise JournalError(
                f"{file}: line {number} is not valid JSON ({error.msg}); "
                "a torn line inside the journal means records were lost, and "
                "guessing which ones would invent history"
            ) from error
        if not isinstance(record, dict) or "event" not in record:
            raise JournalError(f"{file}: line {number} is not a journal record: {line[:80]!r}")
        records.append(record)
    return records


def write(path: str | Path, record: dict[str, Any]) -> None:
    """Append one record and fsync it before returning."""
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(handle, line.encode("utf-8"))
        os.fsync(handle)
    finally:
        os.close(handle)


class Journal:
    """A journal file with the record count kept in memory for cheap appends."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.records = read(self.path)

    def append(self, saga: str, event: str, **fields: Any) -> dict[str, Any]:
        if event not in EVENTS:
            raise JournalError(f"{event!r} is not a journal event; refusing to record a mystery")
        record = {"seq": len(self.records) + 1, "at": _now(), "saga": saga, "event": event}
        record.update(fields)
        write(self.path, record)
        self.records.append(record)
        return record

    def for_saga(self, saga: str) -> list[dict[str, Any]]:
        return [record for record in self.records if record.get("saga") == saga]

    def statuses(self, saga: str) -> dict[str, str]:
        """Per-step status, last event wins except for compensation outcomes."""
        status: dict[str, str] = {}
        for record in self.for_saga(saga):
            name = record.get("step")
            if not isinstance(name, str):
                continue
            event = record["event"]
            if event == "step.retried":
                status.setdefault(name, "interrupted")
                status[name] = "interrupted"
            elif event == "step.started":
                status[name] = "interrupted"
            elif event == STEP_FAILED:
                status[name] = "failed"
            elif event in (STEP_SUCCEEDED, STEP_COMPENSATED, STEP_COMPENSATION_FAILED):
                status[name] = event.split(".", 1)[1]
            elif event == "step.unrecoverable":
                status[name] = "unrecoverable"
        return status

    def outcome(self, saga: str) -> str | None:
        for record in reversed(self.for_saga(saga)):
            if record["event"] in ("saga.completed", "saga.rolled_back", "saga.incomplete"):
                return record["event"].split(".", 1)[1]
        return None
