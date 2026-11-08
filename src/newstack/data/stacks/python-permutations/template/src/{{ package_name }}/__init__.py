"""Small lists, honestly permuted: every ordering, counted and audited.

perm(items) answers every ordering of items, count(n) answers the
factorial count, and audit(items) names any shape that fails. The
promise is checked, never assumed: a permutation keeps every item
exactly once, in a new order, and an oversized or malformed input
is named, never permuted.
"""

from __future__ import annotations

from .solve import (
    MAX_N,
    PermutationError,
    audit,
    count,
    permutations,
    unique,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_N",
    "PermutationError",
    "audit",
    "count",
    "permutations",
    "unique",
]
