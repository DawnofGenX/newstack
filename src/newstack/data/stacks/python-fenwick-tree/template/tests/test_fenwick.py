from __future__ import annotations

import pytest

from {{ package_name }}.fenwick import (
    Fenwick,
    FenwickError,
    build_cells,
    step_of,
)

VALUES = [-5, 0, 3, 11, 7, -2, 18, 26, 9, 40, 14, 63, 5, 31, 22, 57]


def filled() -> Fenwick:
    return Fenwick(VALUES)


def test_the_step_is_the_lowest_set_bit() -> None:
    assert step_of(1) == 1
    assert step_of(6) == 2
    assert step_of(12) == 4
    assert step_of(7) == 1
    with pytest.raises(FenwickError):
        step_of(0)


def test_every_prefix_equals_the_running_list_sum_reference() -> None:
    tree = filled()
    for count in range(len(VALUES) + 1):
        assert tree.prefix(count).answer == sum(VALUES[:count])
    assert tree.invariant()


def test_an_add_shifts_the_mirror_and_the_cells_together() -> None:
    tree = filled()
    walk = tree.add(2, 7)
    assert tree.value(2) == 10
    assert tree.prefix(5).answer == sum(VALUES[:5]) + 7
    assert tree.prefix(16).answer == sum(VALUES) + 7
    assert walk.cells >= 1
    assert tree.invariant()


def test_no_walk_visits_more_cells_than_the_bit_length() -> None:
    tree = Fenwick(list(range(1, 1025)))
    assert tree.limit == 11
    for count in range(1025):
        assert tree.prefix(count).cells <= 11
    for index in range(1024):
        assert tree.add(index, 0).cells <= tree.limit


def test_a_range_is_two_prefixes_and_the_slice_it_names() -> None:
    tree = filled()
    assert tree.range_sum(3, 11).answer == sum(VALUES[3:11])
    assert tree.range_sum(0, 16).answer == sum(VALUES)
    assert tree.range_sum(5, 5).answer == 0
    with pytest.raises(FenwickError):
        tree.range_sum(9, 2)
    with pytest.raises(FenwickError):
        tree.range_sum(0, 17)


def test_the_fold_builds_the_same_cells_as_cell_by_cell_adds() -> None:
    for size in (0, 1, 17, 96):
        values = [index * 7 - 300 for index in range(size)]
        folded = build_cells(values)
        cellwise = [0] * (size + 1)
        for index, value in enumerate(values):
            cell = index + 1
            while cell <= size:
                cellwise[cell] += value
                cell += cell & -cell
        assert folded == cellwise


def test_the_empty_and_lone_trees_answer_honestly() -> None:
    assert Fenwick([]).prefix(0).answer == 0
    assert Fenwick([]).invariant()
    assert len(Fenwick([])) == 0
    assert Fenwick([41]).prefix(1).answer == 41
    assert Fenwick([41]).prefix(0).answer == 0
    with pytest.raises(FenwickError):
        Fenwick([41]).prefix(2)


def test_an_index_outside_the_tree_is_refused_not_folded() -> None:
    tree = filled()
    for stranger in (16, -1, "two", 2.0, True):
        with pytest.raises(FenwickError):
            tree.add(stranger, 1)


def test_a_rebuild_refolds_identical_cells() -> None:
    tree = filled()
    for index in range(len(VALUES)):
        tree.add(index, index * 3 - 20)
    before = tree.cells()
    tree.rebuild()
    assert tree.cells() == before
    assert tree.invariant()
    assert tree.prefix(16).answer == sum(VALUES) + sum(
        index * 3 - 20 for index in range(len(VALUES))
    )
