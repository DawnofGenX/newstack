from __future__ import annotations

from {{ package_name }}.oracle import (
    brute_drain,
    child_indices,
    heap_breaks,
    parent_index,
)


def test_the_drain_is_the_plain_sort() -> None:
    assert brute_drain([5, -2, 5, 0]) == [-2, 0, 5, 5]
    assert brute_drain([]) == []


def test_the_walk_answers_shape_questions() -> None:
    assert parent_index(0) == -1
    assert parent_index(1) == parent_index(2) == 0
    assert parent_index(8) == 3
    assert child_indices(3, 8) == (7,)
    assert child_indices(3, 9) == (7, 8)
    assert child_indices(0, 1) == ()
    assert child_indices(0, 0) == ()


def test_the_checker_names_broken_slots() -> None:
    assert heap_breaks([]) == []
    assert heap_breaks([1]) == []
    assert heap_breaks([1, 2, 3, 4, 5]) == []
    assert heap_breaks([3, 1, 2]) == [0]
    assert heap_breaks([1, 2, 3, 0]) == [1]
    assert heap_breaks([2, 1, 3, 4]) == [0]


def test_the_checker_walks_the_whole_array() -> None:
    # every parent must ride no higher than either child, everywhere
    assert heap_breaks([0, 1, 2, 3, 4, 5, 6, -1, 8, 9, 10, 11, 12]) == [3]
    assert heap_breaks([*range(14)]) == []
