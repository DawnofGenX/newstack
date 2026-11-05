"""Merge rollups that may arrive more than once, and combine them across shards."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .model import Conflict, Rollup, RollupError, Window


@dataclass(frozen=True)
class MergeResult:
    rollups: list[Rollup]
    repeated: int

    def line(self) -> str:
        shards = ", ".join(sorted({piece.shard for piece in self.rollups})) or "-"
        return (
            f"merged {len(self.rollups)} window(s) from {shards}, "
            f"{self.repeated} repeat(s) dropped"
        )


def merge(rollups: Sequence[Rollup]) -> MergeResult:
    """Collapse exact repeats and refuse disagreements.

    Rollups travel over a network that promises at-least-once delivery, so the
    same window can arrive twice. Adding it twice would inflate the traffic, so a
    repeat is dropped — and a repeat that disagrees is a bug in the producer, not
    something to average away.
    """
    index: dict[tuple[str, int], Rollup] = {}
    repeated = 0
    for piece in rollups:
        key = (piece.shard, piece.window.start_us)
        held = index.get(key)
        if held is None:
            index[key] = piece
            continue
        if (
            held.total != piece.total
            or held.samples != piece.samples
            or held.first_us != piece.first_us
            or held.last_us != piece.last_us
            or held.resets != piece.resets
        ):
            raise Conflict(piece.shard, piece.window.start_us, held.total, piece.total)
        repeated += 1
    return MergeResult(
        rollups=[index[key] for key in sorted(index, key=lambda k: (k[1], k[0]))],
        repeated=repeated,
    )


def combine(rollups: Sequence[Rollup]) -> list[Rollup]:
    """Add the shards together, window by window.

    Shards partition the traffic, so totals add. They do not observe the same
    instants, so coverage is the union: the earliest first reading and the latest
    last reading.
    """
    buckets: dict[tuple[str, int], list[Rollup]] = {}
    for piece in rollups:
        buckets.setdefault((piece.name, piece.window.start_us), []).append(piece)
    combined: list[Rollup] = []
    for key in sorted(buckets, key=lambda pair: (pair[1], pair[0])):
        pieces = buckets[key]
        head = pieces[0]
        combined.append(
            Rollup(
                name=head.name,
                shard="*",
                window=head.window,
                total=sum(piece.total for piece in pieces),
                samples=sum(piece.samples for piece in pieces),
                resets=sum(piece.resets for piece in pieces),
                first_us=min(piece.first_us for piece in pieces),
                last_us=max(piece.last_us for piece in pieces),
            )
        )
    return combined


def parse_rollup(payload: object, where: str) -> Rollup:
    """Rebuild a rollup from the JSON this tool prints."""
    if not isinstance(payload, dict):
        raise RollupError(f"{where} is not an object")
    window = payload.get("window")
    if not isinstance(window, dict):
        raise RollupError(f"{where} has no window object")
    try:
        return Rollup(
            name=payload["name"],
            shard=payload["shard"],
            window=Window(start_us=window["start_us"], end_us=window["end_us"]),
            total=payload["total"],
            samples=payload["samples"],
            resets=payload["resets"],
            first_us=payload["first_us"],
            last_us=payload["last_us"],
        )
    except KeyError as error:
        raise RollupError(f"{where} is missing {error.args[0]!r}") from None
    except TypeError as error:
        raise RollupError(f"{where}: {error}") from None


def load(path: Path) -> list[Rollup]:
    """Read a file this tool wrote: a JSON list of rollups."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RollupError(f"cannot read {path}: {error.strerror or error}") from None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise RollupError(f"{path} is not JSON: {error}") from None
    if isinstance(payload, dict) and isinstance(payload.get("rollups"), list):
        payload = payload["rollups"]
    if not isinstance(payload, list):
        raise RollupError(f"{path} does not hold a list of rollups")
    return [
        parse_rollup(entry, f"{path} entry {index}") for index, entry in enumerate(payload)
    ]
