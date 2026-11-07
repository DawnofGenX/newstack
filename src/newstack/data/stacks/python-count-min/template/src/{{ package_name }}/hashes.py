"""Deterministic multiplicative hashes: row r is a bijection on cells.

Every row of the sketch is seated by one multiplier, odd and fixed
for the width, so ``cell = (key * multiplier) % width`` is a pure
permutation on [0, width) whenever the width is a power of two. No
shifting, no truncation, no randomness at run time: the same key and
the same row answer the same cell forever, and the shipped rows are
distinct permutations of the same universe.
"""

from __future__ import annotations

from .keys import UNIVERSE

WIDTH = UNIVERSE
DEPTH = 5

MULTIPLIERS = (37, 71, 109, 151, 199)


def cell_of(key: int, row: int, multipliers: tuple[int, ...], width: int) -> int:
    """The cell a row hands to a key: odd multiplier, exact modulo."""
    return (key * multipliers[row]) % width


def bijective(width: int, multipliers: tuple[int, ...]) -> bool:
    """Whether each row is a permutation on [0, width) (odd, power two)."""
    if width <= 0 or width & (width - 1):
        return False
    return all(multiplier % 2 == 1 for multiplier in multipliers)
