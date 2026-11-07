from __future__ import annotations

from {{ package_name }}.brute import (
    brute_sort,
    is_root,
    root_key,
)
from {{ package_name }}.tree import (
    SplayTree,
)

KEYS = (9, -4, 12, 0, 120)


def test_the_sort_is_the_order() -> None:
    assert brute_sort(KEYS) == sorted(KEYS)
    assert brute_sort([]) == []


def test_the_root_is_read_from_structure() -> None:
    tree = SplayTree([5])
    assert root_key(tree._root) == 5
    assert is_root(tree, 5)
    assert not is_root(tree, 6)


def test_the_root_of_nothing_is_nothing() -> None:
    assert root_key(None) is None
    assert not is_root(SplayTree(), 1)
