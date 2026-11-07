"""Seeded storms of inserts and queries, checked after every op.

The workload is the falsifier with a memory: it drives the tree through
a scripted sequence, and after every single op it re-reads membership,
the rectangle answer, and the nearest answer against a plain list scan.
A break counter the storm cannot push past zero is the only report here
worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .scan import scan_has, scan_nearest, scan_range
from .tree import KDTree

DEFAULT_STEPS = 160


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether anything it answered was wrong."""

    steps: int
    checks: int
    breaks: int
    points: int
    seated: bool


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()

    @property
    def nothing(self) -> None:  # pragma: no cover - shape only
        return None


def run_storm(steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED,
              pool: int = 80) -> Replay:
    """Insert and ask; re-check every answer after every op."""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    corpus = synthetic(pool, seed=seed, span=60)
    tree = KDTree()
    held: set[tuple[int, int]] = set()
    breaks = 0
    checks = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.5:
            point = rng.choice(corpus)
            tree.insert(point)
            held.add(point)
        elif move < 0.65 and held:
            probe = rng.choice(sorted(held))
            checks += 1
            if tree.has(probe) is not scan_has(sorted(held), probe):
                breaks += 1
        elif move < 0.82 and held:
            x, y = rng.choice(sorted(held))
            box = (x - 10, y - 10, x + 10, y + 10)
            checks += 1
            if tree.range(box) != scan_range(sorted(held), box):
                breaks += 1
        elif move < 0.95:
            query = (rng.randint(-70, 70), rng.randint(-70, 70))
            checks += 1
            if tree.nearest(query) != scan_nearest(sorted(held), query):
                breaks += 1
        else:
            victim = rng.choice(corpus)
            tree.insert(victim)
            held.add(victim)
        checks += 1
        if tree.count() != len(held):
            breaks += 1
        checks += 1
        if not tree.invariant():
            breaks += 1
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        points=tree.count(),
        seated=sorted(tree.walk()) == sorted(held),
    )


def rebuild_matches(corpus: list[tuple[int, int]],
                    seed: int = DEFAULT_SEED) -> bool:
    """Two trees fed the same points answer identically, forever after."""
    first = KDTree(corpus)
    second = KDTree(list(reversed(sorted(corpus))))
    rng = random.Random(seed)
    probes = [rng.choice(corpus) for _ in range(40)]
    for probe in probes:
        box = (probe[0] - 5, probe[1] - 5, probe[0] + 5, probe[1] + 5)
        if first.has(probe) != second.has(probe):
            return False
        if first.range(box) != second.range(box):
            return False
        if first.nearest(probe) != second.nearest(probe):
            return False
    return sorted(first.walk()) == sorted(second.walk()) == sorted(set(corpus))
