from __future__ import annotations

import pytest

from {{ package_name }}.btree import BTree, BTreeError

CORPUS = list(range(-30, 70, 3))


def tree(order: int = 3) -> BTree:
    return BTree(order, CORPUS)


def test_a_fresh_tree_is_empty_but_ready() -> None:
    empty = BTree()
    assert empty.keys == []
    assert empty.height == 0
    assert empty.leaf_levels == 0
    assert len(empty) == 0


def test_the_walk_is_the_sorted_corpus() -> None:
    found = tree()
    assert found.keys == sorted(CORPUS)
    assert list(found) == sorted(CORPUS)
    assert len(found) == len(set(CORPUS))


def test_every_node_below_the_root_sits_in_the_band() -> None:
    for order in (2, 3, 5, 13):
        found = BTree(order, range(200))
        for shape in found.shape():
            if shape.depth > 0:
                assert shape.keys >= found.min_keys
            assert shape.keys <= found.max_keys


def test_all_leaves_rest_at_one_level() -> None:
    for order in (2, 3, 5, 13):
        assert BTree(order, range(150)).leaf_levels == 1


def test_a_duplicate_insert_lands_once() -> None:
    found = tree()
    before = len(found)
    assert found.insert(CORPUS[4]) is False
    assert len(found) == before


def test_insert_of_a_foreign_type_is_refused() -> None:
    with pytest.raises(BTreeError):
        tree().insert("seven")  # type: ignore[arg-type]


def test_an_order_below_two_is_refused() -> None:
    with pytest.raises(BTreeError):
        BTree(1)


def test_a_fractional_order_is_refused() -> None:
    with pytest.raises(BTreeError):
        BTree(2.5)  # type: ignore[arg-type]


def test_exact_lookup_answers_for_held_and_missing_keys() -> None:
    found = tree()
    assert found.lookup(CORPUS[10]) is True
    assert found.lookup(4) is False
    assert (4 in found) is False
    assert (CORPUS[0] in found) is True


def test_a_window_answers_ascending_or_refuses_inversion() -> None:
    found = tree()
    assert found.range_scan(-10, 20) == [k for k in sorted(CORPUS) if -10 <= k <= 20]
    assert found.range_scan(5, 5) == []
    with pytest.raises(BTreeError):
        found.range_scan(20, 10)


def test_deleting_every_key_drains_to_nothing() -> None:
    found = tree(2)
    for key in sorted(CORPUS):
        assert found.delete(key) is True
    assert found.keys == []
    assert found.height == 0
    assert found.delete(0) is False


def test_a_split_never_drops_a_key() -> None:
    found = BTree(2)
    for key in range(64):
        found.insert(key)
    assert found.keys == list(range(64))
    assert all(s.keys <= 3 for s in found.shape())


def test_a_merge_never_eats_a_sibling() -> None:
    found = BTree(2, range(32))
    for key in range(0, 32, 2):
        found.delete(key)
    assert found.keys == list(range(1, 32, 2))
    assert found.leaf_levels == 1


def test_the_shape_names_depth_and_band() -> None:
    shapes = BTree(3, range(60)).shape()
    assert shapes[0].depth == 0
    assert any(shape.is_leaf for shape in shapes)
    leaves = [shape for shape in shapes if shape.is_leaf]
    assert {shape.depth for shape in leaves} == {max(s.depth for s in shapes)}
    for shape in shapes:
        if shape.is_leaf:
            assert shape.keys >= 0


def test_a_deep_delete_history_keeps_the_promise() -> None:
    found = BTree(3, range(120))
    for key in range(0, 120, 3):
        found.delete(key)
    for key in range(2, 120, 3):
        found.delete(key)
    assert found.keys == sorted(set(range(120)) - set(range(0, 120, 3)) - set(range(2, 120, 3)))
    assert found.leaf_levels == 1
