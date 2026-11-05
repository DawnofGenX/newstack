"""Parsing NDJSON records, with errors that name the line that broke."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class InputError(ValueError):
    """A record is unusable, and the message says which one and why."""


@dataclass(frozen=True)
class Record:
    id: str
    text: str


def parse_ndjson(raw: str) -> list[Record]:
    """Parse one JSON object per line.

    Blank lines are skipped (a trailing newline is not a record). A malformed line
    is a hard error carrying its 1-based number: silently dropping records from a
    report is worse than refusing to build it.
    """
    records: list[Record] = []
    seen: set[str] = set()
    for number, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise InputError(f"line {number}: not JSON ({error.msg})") from error
        if not isinstance(payload, dict):
            raise InputError(f"line {number}: expected a JSON object, got {type(payload).__name__}")
        identifier = payload.get("id")
        text = payload.get("text")
        if not isinstance(identifier, str) or not identifier.strip():
            raise InputError(f'line {number}: "id" must be a non-empty string')
        if not isinstance(text, str):
            raise InputError(f'line {number}: "text" must be a string')
        if identifier in seen:
            raise InputError(f'line {number}: duplicate id "{identifier}"')
        seen.add(identifier)
        records.append(Record(id=identifier, text=text))
    return records


def read_records(path: Path) -> list[Record]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise InputError(f"{path}: not UTF-8 ({error.reason} at byte {error.start})") from error
    except OSError as error:
        raise InputError(f"{path}: {error.strerror}") from error
    return parse_ndjson(raw)
