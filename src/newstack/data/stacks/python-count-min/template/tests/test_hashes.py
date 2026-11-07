from __future__ import annotations

import pytest

from {{ package_name }}.hashes import (
    DEPTH,
    MULTIPLIERS,
    WIDTH,
    bijective,
    cell_of,
)


def test_the_shipped_shape_is_wide_enough() -> None:
    assert WIDTH == 256
    assert DEPTH == 5
    assert len(MULTIPLIERS) == DEPTH


def test_rows_are_bijections_on_the_cells() -> None:
    assert bijective(WIDTH, MULTIPLIERS)
    for row in range(DEPTH):
        cells = sorted(cell_of(key, row, MULTIPLIERS, WIDTH) for key in range(WIDTH))
        assert cells == list(range(WIDTH))


def test_a_cell_replays_itself() -> None:
    assert cell_of(42, 2, MULTIPLIERS, WIDTH) == cell_of(42, 2, MULTIPLIERS, WIDTH)


def test_a_non_power_shape_is_not_bijective() -> None:
    assert not bijective(50, MULTIPLIERS)
    assert not bijective(64, (2, 5, 7, 11, 13))


@pytest.mark.parametrize("row", list(range(DEPTH)))
def test_multipliers_are_odd(row: int) -> None:
    assert MULTIPLIERS[row] % 2 == 1
