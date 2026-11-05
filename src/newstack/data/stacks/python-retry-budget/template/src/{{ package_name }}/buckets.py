"""Readings arrive as buckets, and a bucket that is missing is not a bucket of zeros."""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_WIDTH_S = 60


class ReadingError(ValueError):
    """A stream of buckets that cannot be trusted."""


@dataclass(frozen=True)
class Bucket:
    at_s: int
    good: int
    bad: int

    @property
    def total(self) -> int:
        return self.good + self.bad

    def line(self, width_s: int = DEFAULT_WIDTH_S) -> str:
        start = datetime.fromtimestamp(self.at_s, tz=UTC)
        return f"{start:%Y-%m-%dT%H:%M:%SZ}  good {self.good:>7}  bad {self.bad:>6}  of {width_s}s"


def _integer(value: object, name: str, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReadingError(f"{where}: {name} must be an integer, got {value!r}")
    if value < 0:
        raise ReadingError(f"{where}: {name} cannot be negative, got {value}")
    return value


def _moment(value: object, width_s: int, where: str) -> int:
    if isinstance(value, bool):
        raise ReadingError(f"{where}: at must be a timestamp, got {value!r}")
    if isinstance(value, int):
        at_s = value
    elif isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ReadingError(f"{where}: at {value!r} is not ISO 8601: {error}") from error
        if moment.tzinfo is None:
            raise ReadingError(f"{where}: at {value!r} has no offset")
        at_s = int(moment.timestamp())
    else:
        raise ReadingError(f"{where}: at must be a timestamp, got {value!r}")
    if at_s % width_s:
        raise ReadingError(
            f"{where}: bucket at {at_s} is not aligned to {width_s}s; an unaligned "
            "bucket makes every window it lands in ambiguous"
        )
    return at_s


def load(path: Path | str, *, width_s: int = DEFAULT_WIDTH_S) -> list[Bucket]:
    """Read JSON Lines; each line is {"at": ..., "good": n, "bad": n}."""
    if width_s < 1:
        raise ReadingError(f"width_s must be at least 1, got {width_s}")
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        raise ReadingError(f"cannot read {source}: {error}") from error
    buckets: dict[int, Bucket] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{source}:{number}"
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ReadingError(f"{where}: not JSON: {error}") from error
        if not isinstance(payload, dict):
            raise ReadingError(f"{where}: a bucket is an object, got {type(payload).__name__}")
        unknown = sorted(set(payload) - {"at", "good", "bad"})
        if unknown:
            raise ReadingError(f"{where}: unknown field(s) {', '.join(unknown)}")
        for required in ("at", "good", "bad"):
            if required not in payload:
                raise ReadingError(f"{where}: missing {required!r}")
        at_s = _moment(payload["at"], width_s, where)
        good = _integer(payload["good"], "good", where)
        bad = _integer(payload["bad"], "bad", where)
        if at_s in buckets:
            raise ReadingError(
                f"{where}: two buckets for {at_s}; a repeated bucket would count the "
                "same traffic twice"
            )
        buckets[at_s] = Bucket(at_s, good, bad)
    if not buckets:
        raise ReadingError(f"{source} has no buckets in it")
    return [buckets[at_s] for at_s in sorted(buckets)]


def span(buckets: list[Bucket], *, width_s: int = DEFAULT_WIDTH_S) -> tuple[int, int]:
    return buckets[0].at_s, buckets[-1].at_s + width_s


def gaps(buckets: list[Bucket], *, width_s: int = DEFAULT_WIDTH_S) -> list[tuple[int, int]]:
    """The stretches with no bucket at all, so silence is never read as success."""
    found: list[tuple[int, int]] = []
    for earlier, later in itertools.pairwise(buckets):
        if later.at_s - earlier.at_s > width_s:
            found.append((earlier.at_s + width_s, later.at_s))
    return found


def between(
    buckets: list[Bucket], start_s: int, end_s: int, *, width_s: int = DEFAULT_WIDTH_S
) -> list[Bucket]:
    """Buckets whose interval falls inside [start_s, end_s)."""
    return [b for b in buckets if start_s <= b.at_s and b.at_s + width_s <= end_s]


def totals(buckets: list[Bucket]) -> tuple[int, int]:
    good = sum(bucket.good for bucket in buckets)
    bad = sum(bucket.bad for bucket in buckets)
    return good, bad
