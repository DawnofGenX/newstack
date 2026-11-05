"""Recompute the chain and compare it with what someone else remembers.

A hash chain proves nothing on its own against an attacker who can also rewrite the hashes. What
it does prove is that nobody has edited the log *without* doing that — and a checkpoint taken
elsewhere turns the rewrite into a detectable event too.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .record import GENESIS, Event, hash_of
from .store import Store

KINDS = ("unreadable", "body-changed", "gap", "chain-broken", "truncated", "rewritten")


@dataclass(frozen=True, slots=True)
class Problem:
    seq: int
    kind: str
    message: str

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(
                f"unknown problem kind {self.kind!r}; expected one of {', '.join(KINDS)}"
            )

    def line(self) -> str:
        return f"seq {self.seq:>4}  {self.kind:<13} {self.message}"


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """What the log looked like when somebody trustworthy last looked."""

    seq: int
    count: int
    hash: str

    def as_dict(self) -> dict[str, Any]:
        return {"format": 1, "seq": self.seq, "count": self.count, "hash": self.hash}

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.as_dict(), indent=2) + "\n")

    @classmethod
    def load(cls, path: Path) -> Checkpoint:
        try:
            data = json.loads(path.read_text())
        except OSError as error:
            raise ValueError(f"cannot read {path}: {error}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"{path} is not JSON: {error}") from error
        if not isinstance(data, dict) or data.get("format") != 1:
            raise ValueError(f"{path} is not a format 1 checkpoint")
        try:
            return cls(seq=int(data["seq"]), count=int(data["count"]), hash=str(data["hash"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path} is missing seq, count or hash: {error}") from error


@dataclass(frozen=True, slots=True)
class Report:
    count: int
    head_seq: int
    head_hash: str
    problems: tuple[Problem, ...]

    @property
    def ok(self) -> bool:
        return not self.problems

    def lines(self) -> list[str]:
        if self.ok:
            return [
                f"verify  ok: {self.count} event(s), head {self.head_seq} {self.head_hash[:16]}…, "
                "every link recomputed"
            ]
        return [f"verify  FAILED: {len(self.problems)} problem(s) in {self.count} event(s)"] + [
            problem.line() for problem in self.problems
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "count": self.count,
            "head_seq": self.head_seq,
            "head_hash": self.head_hash,
            "problems": [
                {"seq": p.seq, "kind": p.kind, "message": p.message} for p in self.problems
            ],
        }


def _recomputed(event: Event) -> str:
    return hash_of(event.body)


def check_chain(events: list[Event]) -> list[Problem]:
    problems: list[Problem] = []
    expected_seq = 1
    expected_prev = GENESIS
    for event in events:
        if event.seq != expected_seq:
            problems.append(
                Problem(event.seq, "gap", f"expected seq {expected_seq}, found {event.seq}")
            )
            expected_seq = event.seq
        fresh = _recomputed(event)
        if fresh != event.hash:
            problems.append(
                Problem(
                    event.seq,
                    "body-changed",
                    f"stored hash {event.hash[:16]}… but the body now hashes to {fresh[:16]}…",
                )
            )
        if event.prev_hash != expected_prev:
            problems.append(
                Problem(
                    event.seq,
                    "chain-broken",
                    f"prev_hash {event.prev_hash[:16]}… is not the previous event's "
                    f"{expected_prev[:16]}…",
                )
            )
        expected_seq += 1
        expected_prev = event.hash
    return problems


def compare_checkpoint(checkpoint: Checkpoint, events: list[Event], count: int) -> list[Problem]:
    """Only failures are reported: a log that grew since the checkpoint is a working log."""
    head = events[-1] if events else None
    if count < checkpoint.count:
        return [
            Problem(
                count + 1,
                "truncated",
                f"the checkpoint recorded {checkpoint.count} event(s), the log now has {count}",
            )
        ]
    if head is None or head.seq < checkpoint.seq:
        return [
            Problem(
                checkpoint.seq,
                "truncated",
                f"the checkpoint recorded seq {checkpoint.seq}, the log now ends at "
                f"{'nothing' if head is None else head.seq}",
            )
        ]
    at = next((event for event in events if event.seq == checkpoint.seq), None)
    if at is None or at.hash != checkpoint.hash:
        return [
            Problem(
                checkpoint.seq,
                "rewritten",
                f"the checkpoint has {checkpoint.hash[:16]}… at seq {checkpoint.seq}, the log has "
                f"{'nothing' if at is None else at.hash[:16] + '…'}",
            )
        ]
    return []


def verify(store: Store, checkpoint: Checkpoint | None = None) -> Report:
    events = store.events()
    count = store.count()
    problems = check_chain(events)
    if checkpoint is not None:
        problems = problems + compare_checkpoint(checkpoint, events, count)
    # One read is a snapshot; a verifier that re-read halfway through would report a chain that
    # never existed.
    head = events[-1] if events else None
    return Report(
        count=len(events),
        head_seq=0 if head is None else head.seq,
        head_hash=GENESIS if head is None else head.hash,
        problems=tuple(problems),
    )


def checkpoint_of(store: Store) -> Checkpoint:
    events = store.events()
    head = events[-1] if events else None
    return Checkpoint(
        seq=0 if head is None else head.seq,
        count=len(events),
        hash=GENESIS if head is None else head.hash,
    )
