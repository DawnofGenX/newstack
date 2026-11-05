"""The SSE wire format, kept separate from the HTTP layer so it can be unit tested.

One event is:

    id: 3
    event: tick
    data: {"seq": 3}
    <blank line>

A field value may not contain a raw newline: any newline inside ``data`` splits the
event, and a client that joins the lines with "\\n" gets something else back. Every
value therefore goes through :func:`encode_field`, which splits on newlines and
repeats the field name, the way the spec requires.
"""

from __future__ import annotations

import json
from collections.abc import Iterable


def encode_field(name: str, value: str) -> str:
    """Encode one field, repeating the name when the value holds a newline."""
    parts = value.split("\n")
    return "".join(f"{name}: {part}\n" for part in parts)


def encode_event(data: str, event: str | None = None, event_id: str | None = None) -> str:
    out = ""
    if event_id is not None:
        out += encode_field("id", event_id)
    if event is not None:
        out += encode_field("event", event)
    out += encode_field("data", data)
    return out + "\n"


def encode_comment(text: str) -> str:
    """A comment keeps proxies and browsers from timing the stream out."""
    return "".join(f": {line}\n" for line in text.split("\n")) + "\n"


def encode_json(payload: object, event: str | None = None, event_id: str | None = None) -> str:
    return encode_event(
        json.dumps(payload, separators=(",", ":"), sort_keys=False), event, event_id
    )


def parse_events(raw: str) -> list[dict[str, str]]:
    """Parse an SSE body into ``{"id", "event", "data"}`` dicts; comments are dropped."""
    events: list[dict[str, str]] = []
    current: dict[str, list[str]] = {}

    def flush() -> None:
        if current:
            events.append({name: "\n".join(lines) for name, lines in current.items()})
            current.clear()

    for line in raw.split("\n"):
        if not line:
            flush()
            continue
        if line.startswith(":"):
            continue
        name, _, value = line.partition(":")
        value = value.removeprefix(" ")
        current.setdefault(name, []).append(value)
    flush()
    return events


def ticks(total: int, size: int, start_at: int = 1) -> Iterable[tuple[int, str]]:
    """Yield ``(sequence number, chunk)`` for *total* ticks, each holding *size* chars."""
    for offset in range(total):
        sequence = start_at + offset
        yield sequence, f"tick-{sequence:03d}"[:size]
