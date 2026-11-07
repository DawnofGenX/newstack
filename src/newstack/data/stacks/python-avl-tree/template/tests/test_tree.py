from __future__ import annotations

import random

import pytest

from {{ package_name }}.brute import (
    factors,
    height_bound,
)
from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.tree import (
    AVLTree,
    TreeError,
)

SEEDS = (7, 23, 91, 1009)
KEYSETS = ((1, 2, 3, 4, 5), (5, 3, 8, 1, 4, 9, 2), (-7, 0, 7))


def test_the_walk_is_the_plain_sort() -> None:
    for keys in KEYSETS:
        assert AVLTree(keys).flatten() == sorted(keys)
    for seed in SEEDS:
        keys = synthetic(24, seed=seed)
        assert AVLTree(keys).flatten() == sorted(keys)


def test_every_factor_sits_inside_one() -> None:
    for seed in SEEDS:
        tree = AVLTree(synthetic(64, seed=seed))
        assert all(abs(factor) <= 1 for factor in factors(tree._root))
        assert tree.audit() == []


def test_insert_is_idempotent() -> None:
    tree = AVLTree([4, 8, 15])
    tree.insert(8)
    tree.insert(8)
    assert tree.flatten() == [4, 8, 15]
    assert len(tree) == 3


def test_remove_of_an_absent_key_raises() -> None:
    tree = AVLTree([1, 2, 3])
    with pytest.raises(TreeError):
        tree.remove(99)
    assert tree.flatten() == [1, 2, 3]


def test_mixed_workload_keeps_the_walk_at_the_sort() -> None:
    for seed in SEEDS:
        rng = random.Random(seed)
        pool = synthetic(48, seed=seed)
        tree = AVLTree()
        live: set[int] = set()
        for _ in range(160):
            if rng.random() < 0.55 or not live:
                key = rng.choice(pool)
                tree.insert(key)
                live.add(key)
            else:
                key = rng.choice(sorted(live))
                tree.remove(key)
                live.discard(key)
            assert tree.flatten() == sorted(live)
            assert all(abs(factor) <= 1 for factor in factors(tree._root))
            assert tree.height <= height_bound(len(live))


def test_a_rebuild_preserves_the_walk() -> None:
    for seed in SEEDS:
        tree = AVLTree(synthetic(40, seed=seed))
        rebuilt = tree.rebuild()
        assert rebuilt.flatten() == tree.flatten()
        assert rebuilt.audit() == []


def test_rising_inserts_stay_under_the_ceiling() -> None:
    tree = AVLTree(range(1, 300))
    assert tree.flatten() == list(range(1, 300))
    assert tree.height <= height_bound(299)


def test_empty_and_single_keys_answer() -> None:
    bare = AVLTree()
    assert bare.flatten() == []
    assert bare.height == 0
    assert 1 not in bare
    assert bare.invariant()
    one = AVLTree([7])
    assert one.flatten() == [7]
    one.remove(7)
    assert len(one) == 0
    assert one.height == 0
