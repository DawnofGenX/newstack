"""The tree itself: integer cells climbed by the lowest bit.

A Fenwick tree answers prefix sums over integer-indexed integer values
by keeping a cell per index and letting the lowest set bit pick the
step: an add walks up the tree one lowest-bit jump at a time, a prefix
walks back down the same ladder, and neither walk ever touches more
than the bit-length of the size. Public indices are zero-based; the
cells underneath are one-based, and an index outside the tree is
refused, never folded.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .values import ensure_value


class FenwickError(ValueError):
    """The index stepped outside what a tree of this size can answer."""


def step_of(index: int) -> int:
    """The lowest set bit: the size of the step an index walks by."""
    if not isinstance(index, int) or isinstance(index, bool):
        raise FenwickError(f"an index must be a whole number, got {index!r}")
    if index < 1:
        raise FenwickError(f"cell {index} has no step, cells start at one")
    return index & -index


@dataclass(frozen=True)
class Walk:
    """What one op cost: the cells it visited and the answer it gave."""

    op: str
    cells: int
    answer: int

    def line(self) -> str:
        return f"{self.op} cells {self.cells} answer {self.answer}"


def build_cells(values: Sequence[int]) -> list[int]:
    """One pass, in place: each cell folds itself into its parent cell.

    A cell at index ``i`` covers the window that ends at ``i`` and
    starts one lowest-bit step below; pushing the finished window up
    into ``i + step(i)`` in index order builds the whole tree in a
    single pass, and the cells come out identical to the tree built by
    one add per value.
    """
    size = len(values)
    cells = [0, *(ensure_value(value) for value in values)]
    for index in range(1, size + 1):
        parent = index + step_of(index)
        if parent <= size:
            cells[parent] += cells[index]
    return cells


class Fenwick:
    """Integer values in, prefix sums out, in a bit-length of steps.

    ``add(i, delta)`` shifts one value and every cell covering it;
    ``prefix(k)`` answers ``sum(values[:k])`` by walking the cells the
    bits of ``k`` name. Indices handed to the tree are zero-based and
    the answer is exact -- the selftest compares every prefix against
    the running list-sum reference after every op.
    """

    def __init__(self, values: Sequence[int] = ()) -> None:
        self._vals = [ensure_value(value) for value in values]
        self._cells = build_cells(self._vals)
        self._longest = 0

    # -- the shape ------------------------------------------------------

    def __len__(self) -> int:
        return len(self._vals)

    def __bool__(self) -> bool:
        return bool(self._vals)

    @property
    def longest_walk(self) -> int:
        """The most cells one op has ever visited on this tree."""
        return self._longest

    @property
    def limit(self) -> int:
        """The bound every walk obeys: the bit-length of the size."""
        return len(self._vals).bit_length()

    def value(self, index: int) -> int:
        """The value sitting at a zero-based index."""
        self._seat(index)
        return self._vals[index]

    def values(self) -> list[int]:
        """Every value, in index order."""
        return list(self._vals)

    def cells(self) -> list[int]:
        """The one-based cells, index zero standing guard at zero."""
        return list(self._cells)

    # -- the ops ----------------------------------------------------------

    def add(self, index: int, delta: int) -> Walk:
        """Shift one value and climb the cells that cover it."""
        self._seat(index)
        step = ensure_value(delta)
        self._vals[index] += step
        cell = index + 1
        visited = 0
        while cell <= len(self._vals):
            self._cells[cell] += step
            visited += 1
            cell += cell & -cell
        self._longest = max(self._longest, visited)
        return Walk(f"add {step} at {index}", visited, self._vals[index])

    def prefix(self, count: int) -> Walk:
        """The sum of the first ``count`` values, walked down the bits."""
        if not isinstance(count, int) or isinstance(count, bool):
            raise FenwickError(f"a count must be a whole number, got {count!r}")
        if not 0 <= count <= len(self._vals):
            raise FenwickError(
                f"a tree of {len(self._vals)} answers counts up to {len(self._vals)}"
            )
        cell = count
        total = 0
        visited = 0
        while cell > 0:
            total += self._cells[cell]
            visited += 1
            cell -= cell & -cell
        self._longest = max(self._longest, visited)
        return Walk(f"prefix {count}", visited, total)

    def range_sum(self, low: int, high: int) -> Walk:
        """The sum of values[low:high] -- two prefixes, never a scan."""
        for edge, name in ((low, "low"), (high, "high")):
            if not isinstance(edge, int) or isinstance(edge, bool):
                raise FenwickError(f"{name} must be a whole number, got {edge!r}")
        if not 0 <= low <= high <= len(self._vals):
            raise FenwickError(
                f"the window [{low}..{high}) sits outside a tree of {len(self._vals)}"
            )
        back = self.prefix(low)
        front = self.prefix(high)
        return Walk(
            f"range {low}..{high}", back.cells + front.cells, front.answer - back.answer
        )

    # -- the invariants -----------------------------------------------------

    def invariant(self) -> bool:
        """Every cell is the window its bits claim, against the mirror.

        The mirror is the plain value list the tree keeps beside the
        cells; a cell that drifted from the window it covers -- by a
        bad climb, a missed fold, a lost add -- is caught here.
        """
        if len(self._cells) != len(self._vals) + 1 or self._cells[0] != 0:
            return False
        for cell in range(1, len(self._vals) + 1):
            floor = cell - step_of(cell)
            if self._cells[cell] != sum(self._vals[floor:cell]):
                return False
        return self._longest <= self.limit or self._longest == 0

    def rebuild(self) -> None:
        """Fold the tree again from the mirror, one pass over the cells."""
        self._cells = build_cells(self._vals)

    def stats(self) -> dict:
        """A snapshot of the tree, for reports that must not lie."""
        return {
            "size": len(self._vals),
            "cells": len(self._cells),
            "limit": self.limit,
            "longest": self._longest,
            "total": self.prefix(len(self._vals)).answer if self._vals else 0,
            "invariant": self.invariant(),
        }

    def lines(self) -> list[str]:
        """A report of the shape: the cells as they stand, in rows."""
        stats = self.stats()
        rows = [
            f"size {stats['size']} cells {stats['cells']}"
            f" walk-limit {stats['limit']} invariant {stats['invariant']}"
        ]
        for start in range(1, len(self._cells), 8):
            row = " ".join(f"{cell:>6}" for cell in self._cells[start : start + 8])
            rows.append(f"  cells {start:>3}  {row}")
        return rows

    def _seat(self, index: int) -> int:
        if not isinstance(index, int) or isinstance(index, bool):
            raise FenwickError(f"an index must be a whole number, got {index!r}")
        if not 0 <= index < len(self._vals):
            raise FenwickError(
                f"index {index} sits outside a tree of {len(self._vals)},"
                " indices run 0 up to the size"
            )
        return index
