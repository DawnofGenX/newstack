"""Small lists, honestly combined: every subset, counted and audited.

combinations(items) answers every subset of items, count(n) answers
the power-of-two count, and audit(items) names any shape that fails.
The promise is checked, never assumed: a combination keeps the
original order and drops some items, and an oversized or malformed
input is named, never combined.
"""

from __future__ import annotations

from .solve import (
    MAX_N,
    CombinationError,
    audit,
    combinations,
    count,
    unique,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_N",
    "CombinationError",
    "audit",
    "combinations",
    "count",
    "unique",
]
