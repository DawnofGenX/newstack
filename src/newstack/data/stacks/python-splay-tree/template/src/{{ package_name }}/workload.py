"""Seeded storms of inserts, deletes, and touches, checked per move.

The workload is the falsifier with a memory: it drives a tree
through a scripted sequence of inserts, removes, accesses, and
walks, and after every step it re-checks the walk against
`sorted(live)` and the splay promise — every access that admitted a
key left that key at the root. A break counter the storm cannot
push past zero is the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .brute import brute_sort, is_root
from .corpus import DEFAULT_SEED, synthetic
from .keys import ensure_key
from .tree import SplayTree, TreeError

DEFAULT_STEPS = 140
MAX_KEY = 2**31 - 1


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any promise it watched broke."""

    steps: int
    checks: int
    breaks: int
    inserts: int
    removals: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def _settle(tree: SplayTree, live: set[int]) -> int:
    """Breaks this position owes: the walk, the links, the size."""
    breaks = 0
    if tree.flatten() != brute_sort(live):
        breaks += 1
    if tree.audit():
        breaks += 1
    return breaks


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 40
) -> Replay:
    """Insert, remove, touch, walk; re-check everything after every move.

    The live set is the dumb shadow: a plain Python set. The tree may
    disagree with its own shadow only by being wrong, and every
    disagreement lands in the break counter. Every access that found
    a key is followed by the root question, because that is the
    promise this tree makes and the storm is where it is kept.
    """
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    pool_keys = synthetic(pool, seed=seed)
    tree = SplayTree()
    live: set[int] = set()
    breaks = 0
    checks = 0
    inserts = 0
    removals = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.40 or not live:
            key = ensure_key(rng.choice(pool_keys))
            tree.insert(key)  # a seated key re-inserts quiet, still rides
            live.add(key)
            inserts += 1
            checks += 2
            if tree.flatten().count(key) != 1:
                breaks += 1  # a double insert sat in twice
            if not is_root(tree, key):
                breaks += 1  # the insert forgot the ride
        elif move < 0.62:
            key = ensure_key(rng.choice(sorted(live)))
            tree.remove(key)
            live.discard(key)
            removals += 1
            checks += 1
            if live and tree.root not in live:
                breaks += 1  # a remove parked a stranger at the root
        elif move < 0.85:
            key = ensure_key(rng.choice(sorted(live)))
            checks += 2
            if not tree.contains(key):
                breaks += 1  # a seated key denied its seat
            if not is_root(tree, key):
                breaks += 1  # the lookup forgot the ride
        else:
            key = ensure_key(rng.choice(pool_keys))
            checks += 1
            if (key in tree) != (key in live):
                breaks += 1  # the passive question got an answer owed
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
        first = SplayTree(keys)
        second = SplayTree(keys)
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
