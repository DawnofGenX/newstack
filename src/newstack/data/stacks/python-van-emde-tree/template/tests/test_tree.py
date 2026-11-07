from __future__ import annotations

import random

import pytest

from {{ package_name }}.brute import (
    scan_member,
    scan_predecessor,
    scan_successor,
)
from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.keys import (
    MAX_KEY,
    UNIVERSE,
)
from {{ package_name }}.tree import (
    TreeError,
    VanEmdeTree,
)

KEYSETS = ((0, 7, 255), (1, 2, 3, 4, 5), (0, 64, 128, 192), tuple(range(0, 256, 17)))
SEEDS = (7, 23, 91, 1009)


def test_successor_and_predecessor_equal_the_scan() -> None:
    for keys in KEYSETS:
        tree = VanEmdeTree(keys)
        for query in range(UNIVERSE):
            assert tree.successor(query) == scan_successor(keys, query)
            assert tree.predecessor(query) == scan_predecessor(keys, query)


def test_membership_is_set_membership_after_every_move() -> None:
    for seed in SEEDS:
        rng = random.Random(seed)
        tree = VanEmdeTree()
        live: set[int] = set()
        for _ in range(120):
            if rng.random() < 0.55 or not live:
                key = rng.randint(0, MAX_KEY)
                tree.insert(key)
                live.add(key)
            else:
                victim = rng.choice(sorted(live))
                tree.remove(victim)
                live.discard(victim)
            assert tree.live() == sorted(live)
            assert len(tree) == len(live)
            probe = rng.randint(0, MAX_KEY)
            assert tree.member(probe) == scan_member(live, probe)
            assert tree.successor(probe) == scan_successor(live, probe)
            assert tree.predecessor(probe) == scan_predecessor(live, probe)
            assert tree.minimum() == (min(live) if live else None)
            assert tree.maximum() == (max(live) if live else None)
            assert tree.invariant()


def test_min_and_max_survive_every_delete() -> None:
    for seed in SEEDS:
        tree = VanEmdeTree(synthetic(40, seed=seed))
        for key in sorted(synthetic(40, seed=seed)):
            tree.remove(key)
            rest = [seat for seat in synthetic(40, seed=seed) if seat > key]
            assert tree.minimum() == (rest[0] if rest else None)
            assert tree.maximum() == (rest[-1] if rest else None)


def test_the_universe_seats_completely() -> None:
    whole = VanEmdeTree(range(UNIVERSE))
    assert len(whole) == UNIVERSE
    assert whole.live() == list(range(UNIVERSE))
    assert whole.successor(MAX_KEY) == MAX_KEY
    assert whole.predecessor(0) == 0
    whole.remove(MAX_KEY)
    assert whole.successor(MAX_KEY) is None
    assert whole.invariant()


def test_empty_answers_none_and_removals_are_refused() -> None:
    bare = VanEmdeTree()
    assert bare.minimum() is None and bare.maximum() is None
    assert bare.successor(0) is None and bare.predecessor(MAX_KEY) is None
    assert not bare.member(0) and bare.live() == []
    with pytest.raises(TreeError):
        bare.remove(0)
    tree = VanEmdeTree([4, 8, 15])
    with pytest.raises(TreeError):
        tree.remove(99)
    assert tree.live() == [4, 8, 15]


def test_insert_is_idempotent_and_rebuild_answers_alike() -> None:
    tree = VanEmdeTree([4, 8, 15])
    tree.insert(8)
    tree.insert(8)
    assert tree.live() == [4, 8, 15] and len(tree) == 3
    twin = tree.rebuild()
    assert twin.live() == tree.live() and twin.invariant()
