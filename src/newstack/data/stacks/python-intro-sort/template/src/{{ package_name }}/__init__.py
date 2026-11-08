"""Small nonneg integer arrays, honestly sorted: the tally, the oracle.

sort(values) answers the sorted list - the same list the dumb
oracle (sorted()) answers - counts(values) answers the honest
per-value tally, and rank(values, value) answers the prefix. The
promise is checked, never assumed: the tally is the histogram, and
a negative or oversized value is named, never sorted.
"""

from __future__ import annotations

from .solve import (
    MAX_VALUE,
    SortError,
    audit,
    counts,
    rank,
    sort,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_VALUE",
    "SortError",
    "audit",
    "counts",
    "rank",
    "sort",
]
