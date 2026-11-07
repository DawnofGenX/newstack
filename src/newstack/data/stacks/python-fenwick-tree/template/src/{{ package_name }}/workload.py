"""Seeded add/sum storms, replayed against the running list-sum truth.

The workload is the falsifiable part: a tree that keeps its answer
through hundreds of seeded adds and prefix queries must return exactly
what the plain list reference returns after every single op, and no
walk may visit more cells than the bit-length of the size.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .fenwick import Fenwick, FenwickError
from .streams import synthetic

STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for in sizes it cannot hold."""


@dataclass(frozen=True)
class Replay:
    """What a storm spent and whether it ever lied."""

    steps: int
    checks: int
    breaks: int
    exact: bool
    longest: int
    limit: int


def run_workload(seed: int = 13, steps: int = STEPS) -> Replay:
    """Add and query a seeded storm, checking against the list after each."""
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 1:
        raise WorkloadError("a storm needs whole-number bounds")
    values = synthetic(steps, seed=seed)
    tree = Fenwick(values)
    mirror = list(values)
    rng = random.Random(seed * 31 + 1)
    checks = 0
    breaks = 0
    for _ in range(steps):
        index = rng.randrange(len(mirror))
        delta = rng.randint(-500, 500)
        tree.add(index, delta)
        mirror[index] += delta
        checks += 1
        count = rng.randrange(len(mirror) + 1)
        answer = tree.prefix(count).answer
        checks += 1
        if answer != sum(mirror[:count]) or not tree.invariant():
            breaks += 1
            break
    return Replay(
        steps,
        checks,
        breaks,
        tree.prefix(len(mirror)).answer == sum(mirror),
        tree.longest_walk,
        tree.limit,
    )


def run_walks(seed: int = 17, size: int = 512) -> Replay:
    """Every prefix and every add visit at most bit-length(size) cells."""
    if not isinstance(seed, int) or not isinstance(size, int) or size < 1:
        raise WorkloadError("the walk census needs whole-number bounds")
    tree = Fenwick(synthetic(size, seed=seed))
    longest = 0
    wrong = 0
    for count in range(size + 1):
        walk = tree.prefix(count)
        longest = max(longest, walk.cells)
        if walk.cells > size.bit_length():
            wrong += 1
    for index in range(size):
        before = tree.longest_walk
        tree.add(index, 1)
        if tree.longest_walk > max(before, size.bit_length()):
            wrong += 1
        tree.add(index, -1)
    return Replay(size, size * 2 + size, wrong, wrong == 0, longest, size.bit_length())


def run_storm(seed: int = 23, steps: int = STEPS) -> Replay:
    """A storm on a growing tree: rebuilds and adds agree cell by cell."""
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 2:
        raise WorkloadError("a rebuild storm needs whole-number bounds")
    values = synthetic(steps, seed=seed)
    tree = Fenwick(values)
    for _ in range(steps // 2):
        tree.rebuild()
        if not tree.invariant():
            return Replay(steps, steps, 1, False, tree.longest_walk, tree.limit)
    return Replay(steps, steps // 2, 0, tree.invariant(), 0, tree.limit)


def ensure_bounds(count: int, size: int) -> int:
    """An honest count for a tree of this size, or the refusal."""
    if not 0 <= count <= size:
        raise FenwickError(f"a tree of {size} answers counts up to {size}")
    return count
