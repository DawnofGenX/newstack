"""Seeded storms of builds and queries, checked after every answer.

The workload is the falsifier with a memory: it drives tables through
a scripted sequence of builds, counts, and asks, and after every step
it re-reads the array, the count, and the tallest neighbour share
against the plain scan. A break counter the storm cannot push past
zero is the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .scan import scan_array, scan_count, scan_lcp_pair, scan_lrs
from .suffix import SuffixArray

DEFAULT_STEPS = 140


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any answer it took was wrong."""

    steps: int
    checks: int
    breaks: int
    builds: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 40
) -> Replay:
    """Build, count, ask; re-check the array and the share after every step."""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    corpus = synthetic(pool, seed=seed)
    table: SuffixArray | None = None
    text = ""
    breaks = 0
    checks = 0
    builds = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.3 or table is None:
            text = rng.choice(corpus)
            table = SuffixArray(text)
            builds += 1
        if table is None:
            continue
        if move < 0.6:
            pattern = text[: rng.randint(1, min(3, len(text)))]
            checks += 1
            if table.count(pattern) != scan_count(text, pattern):
                breaks += 1
        elif move < 0.85:
            checks += 1
            if table.longest_repeat() != scan_lrs(text):
                breaks += 1
        else:
            left = rng.randrange(len(text))
            right = rng.randrange(len(text))
            checks += 1
            if table.lcp(left, right) != scan_lcp_pair(text, left, right):
                breaks += 1
        checks += 1
        if table.array != scan_array(text):
            breaks += 1
        if not table.invariant():
            breaks += 1
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        builds=builds,
        seated=table is None or table.invariant(),
    )


def rebuild_matches(texts: list[str], seed: int = DEFAULT_SEED) -> bool:
    """Two tables over the same texts answer identically, built or rebuilt."""
    for text in texts:
        first = SuffixArray(text)
        second = SuffixArray(text)
        if first.array != second.array:
            return False
        if first.lcp_array() != second.lcp_array():
            return False
        probe = text[: max(1, min(3, len(text)))]
        if first.count(probe) != second.count(probe):
            return False
    return True
