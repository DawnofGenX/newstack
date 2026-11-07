from __future__ import annotations

import pytest

from {{ package_name }}.tree import (
    NEUTRAL,
    SegmentError,
    SegmentTree,
    addition,
    minimum,
)

VALUES = [3, -1, 4, 1, -5, 9, 2, 6, -5, 3, 5, -2]


def filled() -> SegmentTree:
    return SegmentTree(VALUES)


def test_the_root_is_the_whole_array() -> None:
    assert filled().root == sum(VALUES)
    assert filled().n == len(VALUES)


def test_every_window_answers_as_its_slice_sums() -> None:
    tree = filled()
    for low in range(len(VALUES) + 1):
        for high in range(low, len(VALUES) + 1):
            assert tree.query(low, high) == sum(VALUES[low:high])


def test_the_empty_window_answers_the_identity() -> None:
    tree = filled()
    for index in range(len(VALUES) + 1):
        assert tree.query(index, index) == NEUTRAL
        assert tree.visits == 0


def test_a_power_of_two_full_window_visits_once() -> None:
    row = VALUES[:8]
    tree = SegmentTree(row)
    assert tree.query(0, 8) == sum(row)
    assert tree.visits == 1


def test_the_full_window_of_any_array_answers_the_total() -> None:
    tree = filled()
    assert tree.query(0, len(VALUES)) == sum(VALUES)
    assert tree.visits <= 2 * tree.n.bit_length()


def test_no_query_visits_more_than_twice_the_bit_length() -> None:
    tree = filled()
    bound = 2 * tree.n.bit_length()
    for low in range(tree.n + 1):
        for high in range(low, tree.n + 1):
            tree.query(low, high)
            assert tree.visits <= bound


@pytest.mark.parametrize("size", (1, 2, 3, 5, 9, 17, 33))
def test_odd_arrays_answer_the_slices(size: int) -> None:
    row = [index * 3 - 10 for index in range(size)]
    tree = SegmentTree(row)
    assert tree.size == 1 << (size - 1).bit_length()
    for low in range(size + 1):
        for high in range(low, size + 1):
            assert tree.query(low, high) == sum(row[low:high])


def test_set_lands_on_the_leaf_and_refolds_the_path() -> None:
    tree = filled()
    tree.set(4, 40)
    assert tree.leaves()[4] == 40
    assert tree.root == sum(VALUES) + 45
    assert tree.query(3, 6) == 1 + 40 + 9
    assert tree.invariant()


def test_add_slides_the_leaf_and_refolds_the_path() -> None:
    tree = filled()
    landed = tree.add(9, -10)
    assert landed == 3 - 10
    assert tree.leaves()[9] == -7
    assert tree.root == sum(VALUES) - 10
    assert tree.invariant()


def test_an_edit_outside_the_array_is_refused() -> None:
    tree = filled()
    with pytest.raises(SegmentError):
        tree.set(12, 0)
    with pytest.raises(SegmentError):
        tree.add(-1, 1)


def test_a_window_outside_the_array_is_refused() -> None:
    tree = filled()
    with pytest.raises(SegmentError):
        tree.query(5, 3)
    with pytest.raises(SegmentError):
        tree.query(0, 13)


def test_a_rebuild_from_the_leaf_row_equals_the_build() -> None:
    tree = filled()
    tree.set(0, -99)
    tree.add(11, 7)
    rebuilt = SegmentTree(tree.leaves(), tree.combine)
    assert rebuilt.fingerprint() == tree.fingerprint()
    assert rebuilt.query(3, 9) == tree.query(3, 9)


def test_the_combine_is_the_seam() -> None:
    floor = SegmentTree(VALUES, minimum)
    assert floor.query(2, 8) == min(VALUES[2:8])
    assert floor.query(0, 12) == min(VALUES)
    assert addition(3, 4) == 7
    assert minimum(3, 4) == 3


def test_a_stranger_fold_answers_its_own_truth() -> None:
    tree = SegmentTree(VALUES, lambda a, b: a if a >= b else b)
    for low in range(len(VALUES)):
        for high in range(low + 1, len(VALUES) + 1):
            assert tree.query(low, high) == max(VALUES[low:high])


def test_an_array_of_one_is_a_ladder() -> None:
    tree = SegmentTree([7])
    assert tree.query(0, 1) == 7
    assert tree.query(0, 0) == NEUTRAL
    tree.add(0, 1)
    assert tree.root == 8


def test_stats_and_lines_describe_the_ladder_without_lying() -> None:
    tree = filled()
    tree.query(2, 9)
    stats = tree.stats()
    assert stats["n"] == len(VALUES)
    assert stats["root"] == sum(VALUES)
    assert stats["visits"] == tree.visits
    assert stats["invariant"]
    rows = tree.lines()
    assert rows[0].startswith("array  [3, -1")
    assert any(row.startswith("root   ") for row in rows)
