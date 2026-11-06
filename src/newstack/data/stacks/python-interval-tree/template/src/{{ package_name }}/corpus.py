"""Where span lists come from: a fixture file, or a generator the stories trust.

A span list is two integers per line — `start end`. Blank lines and lines
starting with `#` are skipped, so a fixture can carry a comment. The
generator is seeded, so the corpus the selftest proves against is the same
corpus everywhere.
"""

from __future__ import annotations

import random
from pathlib import Path

from .span import Interval

__all__ = ["CorpusError", "load_spans", "synthetic", "write_spans"]


class CorpusError(ValueError):
    """A span list could not be read."""


def load_spans(path: str | Path) -> list[Interval]:
    """Read `start end` per line, skipping blanks and comments."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such span list: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a span list")
    found: list[Interval] = []
    for line in location.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        parts = entry.split()
        if len(parts) != 2:
            raise CorpusError(f"{location} holds {entry!r}, not two integers")
        try:
            found.append(Interval(int(parts[0]), int(parts[1])))
        except ValueError:
            raise CorpusError(f"{location} holds {entry!r}, not two integers") from None
    if not found:
        raise CorpusError(f"{location} holds no spans, and an empty tree stabs nothing")
    return found


def write_spans(intervals: list[Interval], path: str | Path) -> None:
    """Write a span list a later load_spans call reads back exactly."""
    body = "\n".join(f"{span.start} {span.end}" for span in intervals)
    Path(path).write_text(body + "\n", encoding="utf-8")


def synthetic(
    count: int, *, seed: int = 7, low: int = -200, high: int = 200, widest: int = 40
) -> list[Interval]:
    """`count` spans in [low, high), the same list for the same seed."""
    if count < 1:
        raise CorpusError("a corpus of zero spans is not a corpus")
    if high - low < 2:
        raise CorpusError(f"no span fits in [{low}..{high})")
    if widest < 2:
        raise CorpusError("a span at least two points wide is the smallest span")
    rng = random.Random(seed)
    spans: list[Interval] = []
    seen: set[Interval] = set()
    guard = 0
    while len(spans) < count:
        guard += 1
        if guard > count * 40:
            raise CorpusError("this span list will not settle; ask for fewer spans")
        start = rng.randrange(low, high - 1)
        candidate = Interval(start, start + rng.randrange(1, min(widest, high - start)))
        if candidate in seen:
            continue
        seen.add(candidate)
        spans.append(candidate)
    return spans
