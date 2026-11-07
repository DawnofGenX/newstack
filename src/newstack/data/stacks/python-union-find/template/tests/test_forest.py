from __future__ import annotations

import pytest

from {{ package_name }}.forest import (
    Shape,
    UnionFind,
    UnionFindError,
)

CORPUS = list(range(-20, 45, 3))


def forest() -> UnionFind:
    return UnionFind(CORPUS)


def test_a_fresh_forest_holds_nothing() -> None:
    empty = UnionFind()
    assert len(empty) == 0
    assert empty.count == 0
    assert empty.components() == []
    assert empty.shape() == Shape(0, 0, 0, 0)


def test_every_element_starts_alone() -> None:
    found = forest()
    assert found.count == len(set(CORPUS))
    for element in CORPUS:
        assert found.find(element) == element
        assert element in found


def test_add_opens_once() -> None:
    found = forest()
    assert found.add(1000) is True
    assert found.add(1000) is False
    assert len(found) == len(set(CORPUS)) + 1


def test_an_outsider_is_named() -> None:
    with pytest.raises(UnionFindError):
        forest().find(999)


def test_a_bool_is_not_an_element() -> None:
    with pytest.raises(UnionFindError):
        UnionFind([True])  # type: ignore[list-item]


def test_union_merges_once() -> None:
    found = forest()
    assert found.union(CORPUS[0], CORPUS[5]) is True
    assert found.union(CORPUS[0], CORPUS[5]) is False
    assert found.connected(CORPUS[0], CORPUS[5]) is True


def test_union_is_idempotent_under_repeats() -> None:
    found = forest()
    found.union(CORPUS[1], CORPUS[4])
    before = found.components()
    for _ in range(8):
        found.union(CORPUS[1], CORPUS[4])
    assert found.components() == before


def test_transitive_join_shares_one_name() -> None:
    found = forest()
    found.union(CORPUS[0], CORPUS[1])
    found.union(CORPUS[1], CORPUS[2])
    assert found.connected(CORPUS[0], CORPUS[2])
    assert found.find(CORPUS[0]) == found.find(CORPUS[2])


def test_a_join_never_splits() -> None:
    found = forest()
    before = found.components()
    found.union(CORPUS[0], CORPUS[3])
    after = found.components()
    assert len(after) == len(before) - 1
    joined = [group for group in after if CORPUS[0] in group or CORPUS[3] in group]
    assert len(joined) == 1
    assert set(before[0]) <= set(joined[0]) or any(
        set(old) <= set(group) for old in before for group in after
    )


def test_union_by_size_keeps_depth_logarithmic() -> None:
    import math

    for size in (64, 512):
        found = UnionFind(range(size))
        for right in range(1, size):
            found.union(0, right)
        assert found.shape().max_depth <= math.ceil(math.log2(size)) + 1


def test_compression_never_moves_a_component() -> None:
    found = UnionFind(range(6))
    found.union(0, 1)
    found.union(2, 3)
    found.union(0, 2)
    before = found.components()
    names = {element: found.find(element) for element in range(6)}
    assert found.components() == before
    assert {element: found.root_of(element) for element in range(6)} == names


def test_shape_counts_what_a_caller_cannot_see() -> None:
    found = UnionFind(range(10))
    for left, right in ((0, 1), (2, 3), (0, 2)):
        found.union(left, right)
    shape = found.shape()
    assert shape.elements == 10
    assert shape.components == 7
    assert shape.roots_rewritten == 0
    found.find(0)
    assert found.shape().roots_rewritten == 0
    found.find(3)
    assert found.shape().roots_rewritten == 1


def test_components_partition_the_forest() -> None:
    found = forest()
    groups = found.components()
    members = [element for group in groups for element in group]
    assert sorted(members) == sorted(set(CORPUS))
    assert len(groups) == found.count
    assert all(group == sorted(group) for group in groups)


def test_a_snapshot_renders_the_same_partition() -> None:
    found = forest()
    found.union(CORPUS[0], CORPUS[9])
    fresh = UnionFind.from_snapshot(dict(found.snapshot()))
    assert fresh.components() == found.components()
    assert fresh.count == found.count


def test_a_snapshot_needs_one_name_per_element() -> None:
    with pytest.raises(UnionFindError):
        UnionFind.from_snapshot([(1, 1), (2, 2), (1, 2)])
    with pytest.raises(UnionFindError):
        UnionFind.from_snapshot([(1, 7)])
