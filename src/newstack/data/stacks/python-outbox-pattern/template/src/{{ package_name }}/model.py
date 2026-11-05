"""The record of what happened, and the event that says so.

The outbox row is the event: same transaction as the business write, so there is
no window in which the database agrees but the message does not.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

VERSION = 1


class InputError(ValueError):
    """A caller asked for something the schema cannot represent."""


def payload_text(payload: dict[str, Any]) -> str:
    """Canonical JSON, so a retried publish sends the same bytes as the first."""
    if not isinstance(payload, dict):
        raise InputError(f"payload must be a mapping, got {type(payload).__name__}")
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
    except TypeError as error:
        raise InputError(f"payload is not JSON-serialisable: {error}") from error


@dataclass(frozen=True)
class Order:
    ident: int
    amount: int
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.ident, "amount": self.amount, "status": self.status}


@dataclass(frozen=True)
class Event:
    """One fact about one aggregate, with the position it holds in the outbox."""

    event_id: str
    aggregate: str
    seq: int
    kind: str
    payload: dict[str, Any]
    created_at: str
    position: int = 0
    published_at: str | None = None

    @property
    def published(self) -> bool:
        return self.published_at is not None

    def envelope(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "event_id": self.event_id,
            "aggregate": self.aggregate,
            "seq": self.seq,
            "kind": self.kind,
            "payload": self.payload,
            "created_at": self.created_at,
        }

    def line(self) -> str:
        state = "published" if self.published else "pending  "
        head = f"{self.position:>4}  {state}  {self.aggregate:<12} seq {self.seq:>2}"
        return f"{head}  {self.kind:<14} {self.event_id[:12]}"
