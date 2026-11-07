"""The rows are arithmetic: odd multipliers, final seatings, replay."""

from __future__ import annotations

from {{ package_name }}.hashing import (
    LARGE,
    multiplier,
    row_index,
    rows_for,
)

WIDTHS = (8, 64, 1024, 65_536)
SEEDS = (0, 7, 11, 2026)


def test_multipliers_are_odd_and_fit_the_fold() -> None:
    for seed in SEEDS:
        for row in range(16):
            mul = multiplier(row, seed)
            assert mul & 1
            assert mul < LARGE


def test_multipliers_are_distinct_per_row() -> None:
    for seed in SEEDS:
        muls = {multiplier(row, seed) for row in range(16)}
        assert len(muls) == 16


def test_the_fold_is_final() -> None:
    for width in WIDTHS:
        for seed in SEEDS:
            for key in (0, 42, 255):
                for row in range(4):
                    assert 0 <= row_index(key, width, seed, row) < width


def test_a_seating_replays_bit_for_bit() -> None:
    for seed in SEEDS:
        assert rows_for(42, 1024, 4, seed) == rows_for(42, 1024, 4, seed)


def test_a_seating_has_one_seat_per_row() -> None:
    for rows in (1, 4, 16):
        seats = rows_for(200, 1024, rows, 11)
        assert len(seats) == rows
        assert all(0 <= seat < 1024 for seat in seats)
