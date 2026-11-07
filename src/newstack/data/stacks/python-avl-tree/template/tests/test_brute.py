from __future__ import annotations

import math

from {{ package_name }}.brute import (
    brute_sort,
    factors,
    height_bound,
)
from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.tree import (
    AVLTree,
)


def test_the_sort_is_the_builtin_sort() -> None:
    for keys in ([3, -1, 0], [], [7], list(range(50, 0, -7))):
        assert brute_sort(keys) == sorted(keys)


def test_the_ceiling_is_the_ceiling() -> None:
    for count in (0, 1, 2, 10, 1000):
        want = math.ceil(1.44 * math.log2(count + 2))
        assert height_bound(count) == want


def test_the_walk_reads_the_stored_shape() -> None:
    tree = AVLTree([5, 3, 8, 1, 4, 9, 2])
    assert len(factors(tree._root)) == 7
    assert all(abs(factor) <= 1 for factor in factors(tree._root))


def test_the_bound_holds_over_seeded_trees() -> None:
    for seed in (3, 33, 333):
        keys = synthetic(120, seed=seed)
        tree = AVLTree(keys)
        assert tree.height <= height_bound(len(keys))
