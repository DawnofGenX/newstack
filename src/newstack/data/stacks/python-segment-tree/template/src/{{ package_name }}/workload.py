"""Seeded storms of edits and queries, replayed against the slice truth.

The workload is the falsifiable part: a ladder that survives 160
seeded sets, adds, and window queries must answer every window exactly
as the matching slice sums, every visit must fit the bit-length bound,
and the leaf row must rebuild the ladder it came from.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .array import synthetic
from .tree import SegmentTree

STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for in sizes it cannot hold."""


@dataclass(frozen=True)
class Replay:
    """What a storm spent and whether it ever disagreed with the slices."""

    steps: int
    checks: int
    breaks: int
    max_visits: int
    bound: int
    exact: bool
    rebuild_equal: bool


def run_workload(seed: int = 13, steps: int = STEPS) -> Replay:
    """Set, add, and query a seeded ladder, checking every answer exactly."""
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 1:
        raise WorkloadError("a storm needs whole-number bounds")
    mirror = synthetic(steps, seed=seed)
    tree = SegmentTree(mirror)
    rng = random.Random(seed)
    bound = 2 * tree.n.bit_length()
    checks = 0
    breaks = 0
    max_visits = 0
    exact = True
    for _ in range(steps):
        move = rng.randrange(6)
        index = rng.randrange(tree.n)
        low = rng.randrange(tree.n + 1)
        high = rng.randrange(low, tree.n + 1)
        if move == 0:
            tree.set(index, rng.randrange(-500, 500))
            mirror[index] = tree.leaves()[index]
        elif move == 1:
            tree.add(index, rng.randrange(-25, 25))
            mirror[index] = tree.leaves()[index]
        else:
            answer = tree.query(low, high)
            checks += 1
            max_visits = max(max_visits, tree.visits)
            if answer != sum(mirror[low:high]) or tree.visits > bound:
                exact = False
                breaks += 1
                break
            if not tree.invariant():
                breaks += 1
                break
    while checks <= 2 * steps:
        low = rng.randrange(tree.n + 1)
        high = rng.randrange(low, tree.n + 1)
        if tree.query(low, high) != sum(mirror[low:high]):
            exact = False
            breaks += 1
            break
        checks += 1
        max_visits = max(max_visits, tree.visits)
        if tree.visits > bound:
            exact = False
            breaks += 1
            break
    rebuilt = SegmentTree(tree.leaves(), tree.combine)
    return Replay(
        steps,
        checks,
        breaks,
        max_visits,
        bound,
        exact and tree.invariant(),
        rebuilt.fingerprint() == tree.fingerprint(),
    )


def run_bound(size: int = 96, seed: int = 11) -> Replay:
    """Answer every window of one seeded array; no visit may miss the bound."""
    if not isinstance(size, int) or size < 1:
        raise WorkloadError("a bound needs a whole-number size")
    values = synthetic(size, seed=seed)
    tree = SegmentTree(values)
    bound = 2 * tree.n.bit_length()
    checks = 0
    breaks = 0
    max_visits = 0
    exact = True
    for low in range(tree.n + 1):
        for high in range(low, tree.n + 1):
            exact = exact and tree.query(low, high) == sum(values[low:high])
            max_visits = max(max_visits, tree.visits)
            if tree.visits > bound:
                breaks += 1
            checks += 1
    return Replay(
        size, checks, breaks, max_visits, bound,
        exact and breaks == 0, tree.invariant(),
    )
