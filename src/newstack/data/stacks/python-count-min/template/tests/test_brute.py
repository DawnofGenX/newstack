from __future__ import annotations

import pytest

from {{ package_name }}.brute import min_of_rows, true_counts

ROWS = [[5, 2, 9], [4, 8, 1], [6, 3, 7]]
CELLS = [0, 1, 0]


def test_the_ledger_sums_without_structure() -> None:
    assert true_counts([(7, 3), (7, 1), (0, 4)]) == {7: 4, 0: 4}
    assert true_counts([]) == {}


def test_the_min_is_read_straight_off_the_grid() -> None:
    assert min_of_rows(ROWS, CELLS) == 5


def test_the_max_is_not_the_promise() -> None:
    from {{ package_name }}.brute import max_of_rows

    assert max_of_rows(ROWS, CELLS) == 8
    assert max_of_rows(ROWS, CELLS) > min_of_rows(ROWS, CELLS)


def test_a_single_row_answers_itself() -> None:
    assert min_of_rows([[4]], [0]) == 4


def test_cells_must_match_rows() -> None:
    with pytest.raises(ValueError):
        min_of_rows(ROWS, CELLS[:1])
