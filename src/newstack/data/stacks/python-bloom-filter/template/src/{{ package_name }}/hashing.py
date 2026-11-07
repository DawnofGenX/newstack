"""Deterministic multiplicative rows: the count-min family's arithmetic.

One multiply seats a key in a row — ``h_i(x) = (x + 1) * A_i mod
LARGE % width`` — with every multiplier odd (so the walk cannot
collapse onto short bit patterns), distinct per row (so the rows
are genuinely separate seats), and derived from a seed by plain
arithmetic (so the same seed replays the same table forever). No
digest, no randomness at call time: an audit can list every row of
every key in the universe and know the list is final.
"""

from __future__ import annotations

LARGE = (1 << 61) - 1  # a Mersenne prime: the multiply never wraps softly
BASE = 1_000_003
STEP = 7919


def _odd(value: int) -> int:
    """Force odd: an even multiplier folds keys onto short patterns."""
    return value | 1


def multiplier(row: int, seed: int) -> int:
    """The multiplier for one row of one seed: odd, distinct, final."""
    return _odd(BASE + 2 * seed + STEP * (2 * row + 1))


def row_index(key: int, width: int, seed: int, row: int) -> int:
    """Where one row seats one key: multiply, fold, seat."""
    return (key + 1) * multiplier(row, seed) % LARGE % width


def rows_for(key: int, width: int, rows: int, seed: int) -> tuple[int, ...]:
    """Every row of one key, in row order — the whole seating."""
    return tuple(row_index(key, width, seed, row) for row in range(rows))
