"""One event in the log: its body, its hash, and the link to the event before it."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .canon import CanonError, canonical, digest

GENESIS = "0" * 64
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$")


def now_iso() -> str:
    """UTC with an explicit offset, because a local timestamp in an audit log is a bug."""
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class Event:
    """`seq` orders the log; `at` only describes when, because clocks go backwards."""

    seq: int
    at: str
    actor: str
    action: str
    target: str
    detail: dict[str, Any]
    prev_hash: str
    hash: str

    @property
    def body(self) -> dict[str, Any]:
        """Everything the hash covers — and nothing else."""
        return {
            "seq": self.seq,
            "at": self.at,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "detail": self.detail,
            "prev_hash": self.prev_hash,
        }

    def lines(self) -> list[str]:
        return [
            f"seq     {self.seq}",
            f"at      {self.at}",
            f"actor   {self.actor}",
            f"action  {self.action}",
            f"target  {self.target}",
            f"detail  {canonical(self.detail)}",
            f"prev    {self.prev_hash}",
            f"hash    {self.hash}",
        ]


def body_of(
    seq: int,
    actor: str,
    action: str,
    target: str,
    *,
    detail: dict[str, Any] | None = None,
    prev_hash: str = GENESIS,
    at: str | None = None,
) -> dict[str, Any]:
    """Build the hashed body, validating as it goes."""
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
        raise ValueError(f"seq must be a positive integer, got {seq!r}")
    if prev_hash != GENESIS and not re.fullmatch(r"[0-9a-f]{64}", prev_hash):
        raise ValueError("prev_hash must be 64 lowercase hex characters or the GENESIS marker")
    payload = detail if detail is not None else {}
    if not isinstance(payload, dict):
        raise ValueError(f"detail must be a mapping, got {type(payload).__name__}")
    stamp = at if at is not None else now_iso()
    if not ISO.match(stamp):
        raise ValueError(f"at must be an ISO-8601 UTC timestamp, got {stamp!r}")
    body = {
        "seq": seq,
        "at": stamp,
        "actor": _required_text("actor", actor),
        "action": _required_text("action", action),
        "target": _required_text("target", target),
        "detail": payload,
        "prev_hash": prev_hash,
    }
    canonical(body)  # refuse a payload a verifier in another language could not reproduce
    return body


def hash_of(body: dict[str, Any]) -> str:
    try:
        return digest(body)
    except CanonError as error:
        raise ValueError(str(error)) from error


def event_of(body: dict[str, Any]) -> Event:
    return Event(
        seq=body["seq"],
        at=body["at"],
        actor=body["actor"],
        action=body["action"],
        target=body["target"],
        detail=body["detail"],
        prev_hash=body["prev_hash"],
        hash=hash_of(body),
    )


def stored_event(body_text: str, stored_hash: str) -> Event:
    """Rebuild an event exactly as it was stored — the stored hash, not a recomputation.

    Verification must compare the stored hash with a fresh one; if this function recomputed it,
    every forged row would look valid by construction.
    """
    try:
        body = json.loads(body_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"stored body is not JSON: {error}") from error
    if not isinstance(body, dict):
        raise ValueError("stored body is not an object")
    missing = [
        key for key in ("seq", "at", "actor", "action", "target", "detail") if key not in body
    ]
    if missing:
        raise ValueError(f"stored body is missing {', '.join(missing)}")
    return Event(
        seq=body["seq"],
        at=body["at"],
        actor=body["actor"],
        action=body["action"],
        target=body["target"],
        detail=body["detail"],
        prev_hash=body.get("prev_hash", GENESIS),
        hash=stored_hash,
    )
