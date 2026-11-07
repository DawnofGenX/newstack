"""Seeded storms of inserts, deletes, and seeks, checked every step.

The workload is the falsifier with a memory: it drives a tree through
a scripted sequence and, after every move, re-answers min, max,
membership, successor, and predecessor against the brute-force scans
of the live list. A break counter the storm cannot push past zero is
the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .brute import (
    brute_sort,
    scan_member,
    scan_predecessor,
    scan_successor,
)
from .corpus import DEFAULT_SEED, synthetic
from .keys import MAX_KEY, ensure_key
from .tree import VanEmdeTree

DEFAULT_STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any answer it took was wrong."""

    steps: int
    checks: int
    breaks: int
    inserts: int
    removals: int
    seeks: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def _settle(tree: VanEmdeTree, live: set[int]) -> int:
    """Breaks this position owes: every answer against the scan."""
    breaks = 0
    seats = brute_sort(live)
    if tree.live() != seats:
        breaks += 1
    if len(tree) != len(live):
        breaks += 1
    if tree.minimum() != (seats[0] if seats else None):
        breaks += 1
    if tree.maximum() != (seats[-1] if seats else None):
        breaks += 1
    if not tree.invariant():
        breaks += 1
    for probe in (0, MAX_KEY, *seats):
        if tree.successor(probe) != scan_successor(live, probe):
            breaks += 1
        if tree.predecessor(probe) != scan_predecessor(live, probe):
            breaks += 1
    return breaks


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 48
) -> Replay:
    """Insert, remove, seek, re-check; the scan is the only witness.

    The live set is the dumb shadow: a plain Python set with sorted
    scans. The tree may disagree with its own shadow only by being
    wrong, and every disagreement lands in the break counter.
    """
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    pool_keys = synthetic(pool, seed=seed)
    tree = VanEmdeTree()
    live: set[int] = set()
    breaks = 0
    checks = 0
    inserts = 0
    removals = 0
    seeks = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.45 or not live:
            key = ensure_key(rng.choice(pool_keys))
            tree.insert(key)
            live.add(key)
            inserts += 1
        elif move < 0.75:
            victim = rng.choice(brute_sort(live))
            tree.remove(victim)
            live.discard(victim)
            removals += 1
        else:
            probe = ensure_key(rng.randint(0, MAX_KEY))
            seeks += 1
            if tree.successor(probe) != scan_successor(live, probe):
                breaks += 1
            if tree.predecessor(probe) != scan_predecessor(live, probe):
                breaks += 1
            if tree.member(probe) != scan_member(live, probe):
                breaks += 1
        checks += 1
        breaks += _settle(tree, live)
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        inserts=inserts,
        removals=removals,
        seeks=seeks,
        seated=tree.invariant(),
    )


def rebuild_matches(keys: list[int]) -> bool:
    """A rebuilt tree answers exactly like the seated one."""
    tree = VanEmdeTree(keys)
    twin = tree.rebuild()
    return tree.live() == twin.live() and tree.invariant() and twin.invariant()
