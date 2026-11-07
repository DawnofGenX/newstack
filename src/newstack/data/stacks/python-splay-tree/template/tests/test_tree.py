from __future__ import annotations

import random

import pytest

from {{ package_name }}.brute import (
    is_root,
)
from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.tree import (
    SplayTree,
    TreeError,
)

SEEDS = (7, 23, 91, 1009)
KEYSETS = ((1, 2, 3, 4, 5), (5, 3, 8, 1, 4, 9, 2), (-7, 0, 7))


def test_the_walk_is_the_plain_sort() -> None:
    for keys in KEYSETS:
        assert SplayTree(keys).flatten() == sorted(keys)
    for seed in SEEDS:
        keys = synthetic(24, seed=seed)
        assert SplayTree(keys).flatten() == sorted(keys)


def test_every_access_leaves_the_key_at_the_root() -> None:
    for seed in SEEDS:
        tree = SplayTree(synthetic(32, seed=seed))
        for key in tree:
            assert tree.contains(key)
            assert is_root(tree, key)
        assert tree.audit() == []


def test_a_splay_preserves_the_walk() -> None:
    for seed in SEEDS:
        tree = SplayTree(synthetic(24, seed=seed))
        before = tree.flatten()
        for key in sorted(before, reverse=True):
            tree.contains(key)
            assert tree.flatten() == before


def test_insert_is_idempotent_and_rides() -> None:
    tree = SplayTree([4, 8, 15])
    tree.insert(8)
    tree.insert(8)
    assert tree.flatten() == [4, 8, 15]
    assert len(tree) == 3
    assert tree.root == 8


def test_remove_of_an_absent_key_raises() -> None:
    tree = SplayTree([1, 2, 3])
    with pytest.raises(TreeError):
        tree.remove(99)
    assert tree.flatten() == [1, 2, 3]


def test_min_and_max_walk_to_the_root() -> None:
    for seed in SEEDS:
        keys = synthetic(20, seed=seed)
        tree = SplayTree(keys)
        assert tree.minimum() == min(keys)
        assert tree.root == min(keys)
        assert tree.maximum() == max(keys)
        assert tree.root == max(keys)


def test_mixed_workload_keeps_the_walk_at_the_sort() -> None:
    for seed in SEEDS:
        rng = random.Random(seed)
        pool = synthetic(48, seed=seed)
        tree = SplayTree()
        live: set[int] = set()
        for _ in range(160):
            if rng.random() < 0.55 or not live:
                key = rng.choice(pool)
                tree.insert(key)
                live.add(key)
                assert tree.root == key
            else:
                key = rng.choice(sorted(live))
                tree.remove(key)
                live.discard(key)
            assert tree.flatten() == sorted(live)
            assert tree.audit() == []
