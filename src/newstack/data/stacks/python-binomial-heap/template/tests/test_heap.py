from __future__ import annotations

import pytest

from {{ package_name }}.heap import (
    BinomialHeap,
    Edit,
    HeapError,
    Tree,
    link,
    ranks_of,
)

KEYS = [-77, 0, 4, 15, 17, 30, 63, 64, 100, 255, 256, 500, 1023, 2047, 4095]


def filled() -> BinomialHeap:
    heap = BinomialHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
    return heap


def test_a_tree_of_rank_k_holds_exactly_two_to_k_keys() -> None:
    tree = Tree(7, None)
    assert tree.rank == 0
    assert tree.count() == 1
    joined = link(Tree(3, None), Tree(9, None))
    assert joined.rank == 1
    assert joined.count() == 2
    assert joined.key == 3
    assert joined.children[0].key == 9


def test_the_smaller_root_stays_on_top() -> None:
    joined = link(Tree(9, None), Tree(3, None))
    assert joined.key == 3
    assert joined.children[0].key == 9


def test_the_ranks_are_the_bit_pattern() -> None:
    assert ranks_of(0) == []
    assert ranks_of(7) == [0, 1, 2]
    assert ranks_of(8) == [3]
    assert ranks_of(47) == [0, 1, 2, 3, 5]


def test_draining_is_the_sorted_corpus() -> None:
    heap = filled()
    assert list(heap.pop_all()) == sorted(KEYS)
    assert len(heap) == 0
    assert not heap


def test_the_forest_stands_one_tree_per_rank() -> None:
    heap = filled()
    assert heap.shape() == ranks_of(len(heap))
    assert heap.invariant()
    for _ in range(6):
        heap.pop()
        assert heap.shape() == ranks_of(len(heap))
        assert heap.invariant()


def test_the_count_walks_with_the_forest() -> None:
    heap = BinomialHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
        assert len(heap) == index + 1
        assert heap.shape() == ranks_of(index + 1)


def test_meld_unions_and_empties_the_donor() -> None:
    left = BinomialHeap()
    right = BinomialHeap()
    for key in (5, 1, 9):
        left.push(key, key)
    for key in (-4, 12, 300, 700):
        right.push(key, key)
    left.meld(right)
    assert len(left) == 7
    assert len(right) == 0
    assert left.shape() == ranks_of(7)
    assert left.peek()[0] == -4
    assert list(left.pop_all()) == sorted([5, 1, 9, -4, 12, 300, 700])


def test_meld_reports_itself() -> None:
    left = BinomialHeap()
    left.push(1, None)
    right = BinomialHeap()
    right.push(2, None)
    edit = left.meld(right)
    assert isinstance(edit, Edit)
    assert edit.op == "meld"
    assert left.melds == 1


def test_pop_min_of_a_meld_is_the_min_of_the_union() -> None:
    left = BinomialHeap()
    right = BinomialHeap()
    for key in (4, -3, 12):
        left.push(key, None)
    right.push(9, None)
    left.meld(right)
    assert left.peek()[0] == -3
    assert left.pop()[0] == -3


def test_a_heap_will_not_meld_with_itself() -> None:
    heap = filled()
    with pytest.raises(HeapError):
        heap.meld(heap)


def test_an_empty_forest_refuses() -> None:
    heap = BinomialHeap()
    with pytest.raises(HeapError):
        heap.pop()
    with pytest.raises(HeapError):
        heap.peek()


def test_a_non_number_is_no_key() -> None:
    heap = BinomialHeap()
    with pytest.raises(HeapError):
        heap.push(True)
    with pytest.raises(HeapError):
        heap.push("seven")


def test_push_names_the_rank_the_key_reached() -> None:
    heap = BinomialHeap()
    edit = heap.push(30, None)
    assert edit.op == "push"
    assert edit.rank == 0
    assert not edit.linked
    assert edit.line() == "push rank 0 linked=False"
