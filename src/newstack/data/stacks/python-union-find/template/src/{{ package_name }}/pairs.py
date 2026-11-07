"""Workload files: the pairs a forest is built from, and a generator.

A workload is one pair per line, ``a b`` with a space between. Blank
lines and ``#`` comments are skipped. The fixture and the generator both
land here so the smoke test and the selftest can rebuild the same forest.
"""

from __future__ import annotations

import random
from pathlib import Path

__all__ = ["PairError", "load_pairs", "synthetic"]


class PairError(ValueError):
    """A workload file could not be read."""


def load_pairs(path: str | Path) -> list[tuple[int, int]]:
    """Read one ``a b`` pair per line, skipping blanks and comments."""
    location = Path(path)
    if not location.exists():
        raise PairError(f"no such workload: {location}")
    if location.is_dir():
        raise PairError(f"{location} is a directory, not a workload")
    found: list[tuple[int, int]] = []
    for line in location.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        parts = entry.split()
        if len(parts) != 2:
            raise PairError(f"{location} holds {entry!r}, which is not a pair")
        try:
            found.append((int(parts[0]), int(parts[1])))
        except ValueError:
            raise PairError(f"{location} holds {entry!r}, which is not a pair") from None
    if not found:
        raise PairError(f"{location} holds no pairs, and a forest of nothing joins nothing")
    return found


def synthetic(
    count: int,
    *,
    seed: int = 7,
    low: int = 0,
    high: int = 200,
) -> list[tuple[int, int]]:
    """``count`` pairs drawn from [low, high), fixed for a fixed seed."""
    if count < 1:
        raise PairError("a workload of zero pairs is not a workload")
    if low >= high:
        raise PairError(f"an empty span: {low} sits at or above {high}")
    rng = random.Random(seed)
    return [(rng.randrange(low, high), rng.randrange(low, high)) for _ in range(count)]
