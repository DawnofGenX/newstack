"""Seeded storms of inserts, removals, and asks, checked after every op.

The workload is the falsifier with a memory: it drives the tree through
a scripted sequence of adds and removals, and after every single op it
re-reads the walk against ``sorted`` of the live keys and the shape
against the checker. A break counter the storm cannot push past zero is
the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .tree import RBTree

DEFAULT_SEED = 17
DEFAULT_STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for a script it cannot write."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether anything it answered was wrong."""

    steps: int
    checks: int
    breaks: int
    keys: int
    seated: bool


def run_storm(steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED,
              pool: int = 80) -> Replay:
    """Add, remove, ask; re-check the walk and the shape after every op."""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    corpus = list(range(-pool, pool))
    tree = RBTree()
    live: set[int] = set()
    breaks = 0
    checks = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.5:
            key = rng.choice(corpus)
            stored = tree.insert(key)
            if stored is not (key not in live):
                breaks += 1
            live.add(key)
        elif move < 0.8 and live:
            victim = rng.choice(sorted(live))
            tree.remove(victim)
            live.discard(victim)
        else:
            probe = rng.randint(-pool - 10, pool + 10)
            checks += 1
            if tree.has(probe) is not (probe in live):
                breaks += 1
        checks += 1
        if tree.keys() != sorted(live):
            breaks += 1
        checks += 1
        if not tree.invariant():
            breaks += 1
        checks += 1
        if tree.count() != len(live):
            breaks += 1
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        keys=tree.count(),
        seated=tree.keys() == sorted(live) and tree.invariant(),
    )


def rebuild_matches(keys: list[int], seed: int = DEFAULT_SEED) -> bool:
    """Two trees fed the same keys in different orders answer identically."""
    first = RBTree(keys)
    second = RBTree(list(reversed(sorted(keys))))
    rng = random.Random(seed)
    probes = [rng.choice(keys) for _ in range(40)] + [0, 10**9, -10**9]
    for probe in probes:
        if first.has(probe) is not second.has(probe):
            return False
    if first.keys() != second.keys():
        return False
    return first.keys() == sorted(set(keys)) and first.invariant()
