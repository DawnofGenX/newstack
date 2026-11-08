"""Small sorted nonneg integer arrays, honestly searched: the pivot, the discard.

search(values, target) answers the index of target in a sorted
array, contains reports presence, and lower_bound answers the first
index whose value is >= target. The promise is checked, never
assumed: the middle is the pivot, and a missing or unsorted input
is named, never searched.
"""

from __future__ import annotations

from .solve import (
    MAX_VALUE,
    SearchError,
    audit,
    contains,
    lower_bound,
    search,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_VALUE",
    "SearchError",
    "audit",
    "contains",
    "lower_bound",
    "search",
]
