"""Seeded storms of inserts and deletes, checked after every move.

The workload is the falsifier with a memory: it drives a tree through
a scripted sequence of inserts, removes, lookups, and walks, and
after every step it re-checks the walk against `sorted(live)`, every
balance factor against the raw structural walk, and the height
against the AVL ceiling. A break counter the storm cannot push past
zero is the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .brute import brute_sort, factors, height_bound
from .corpus import DEFAULT_SEED, synthetic
from .keys import ensure_key
from .tree import AVLTree, TreeError

DEFAULT_STEPS = 140
MAX_KEY = 2**31 - 1


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
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def _settle(tree: AVLTree, live: set[int]) -> int:
    """Breaks this position owes: walk, factors, heights, bound."""
    breaks = 0
    if tree.flatten() != brute_sort(live):
        breaks += 1
    if any(abs(factor) > 1 for factor in factors(tree._root)):
        breaks += 1
    if tree.height > height_bound(len(live)):
        breaks += 1
    return breaks


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 40
) -> Replay:
    """Insert, remove, look up, walk; re-check everything after every move.

    The live set is the dumb shadow: a plain Python set. The tree may
    disagree with its own shadow only by being wrong, and every
    disagreement lands in the break counter.
"""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    pool_keys = synthetic(pool, seed=seed)
    tree = AVLTree()
    live: set[int] = set()
    breaks = 0
    checks = 0
    inserts = 0
    removals = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.45 or not live:
            key = ensure_key(rng.choice(pool_keys))
            tree.insert(key)  # a seated key re-inserts quiet
            live.add(key)
            inserts += 1
            checks += 1
            if tree.flatten().count(key) != 1:
                breaks += 1  # a double insert sat in twice
        elif move < 0.75:
            key = ensure_key(rng.choice(sorted(live)))
            tree.remove(key)
            live.discard(key)
            removals += 1
        else:
            key = ensure_key(rng.choice(pool_keys))
            checks += 1
            if (key in tree) != (key in live):
                breaks += 1
            if key not in live:
                checks += 1
                try:
                    tree.remove(key)
                    breaks += 1  # an absent remove stayed quiet
                except TreeError:
                    pass
        checks += 2
        breaks += _settle(tree, live)
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        inserts=inserts,
        removals=removals,
        seated=tree.invariant(),
    )


def rebuild_matches(counts: list[int], seed: int = DEFAULT_SEED) -> bool:
    """Two trees answer alike, and a rebuild from the walk answers alike."""
    for count in counts:
        keys = synthetic(count, seed=seed)
        first = AVLTree(keys)
        second = AVLTree(keys)
        if first.flatten() != second.flatten():
            return False
        if first.audit() or second.audit():
            return False
        rebuilt = first.rebuild()
        if rebuilt.flatten() != first.flatten():
            return False
        if rebuilt.audit():
            return False
    return True
