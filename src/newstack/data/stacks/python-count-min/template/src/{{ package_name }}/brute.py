"""The oracles: a plain counter and the min of rows read from raw cells.

Every answer the sketch gives must equal what this module answers on
the same events. The truth is a dict summed with no cleverness at
all; the min is read straight off the shipped grid. The sketch
cannot grade its own homework from here.
"""

from __future__ import annotations

from typing import Any


def true_counts(events: Any) -> dict[int, int]:
    """The ledger answer: key -> exact total, no structure involved."""
    truth: dict[int, int] = {}
    for key, n in events:
        truth[key] = truth.get(key, 0) + n
    return truth


def min_of_rows(rows: Any, cells: Any) -> int:
    """The min of one row's cell per row — the answer the sketch owes."""
    return min(row[cell] for row, cell in zip(rows, cells, strict=True))


def max_of_rows(rows: Any, cells: Any) -> int:
    """The max across rows: the drift side. Min is the promise, max isn't."""
    return max(row[cell] for row, cell in zip(rows, cells, strict=True))
