"""Bracket matching over small strings.

is_valid(text) answers whether every bracket closes in the right
order, matched_pairs lists the matching pairs, count_unmatched
counts the strays, and audit stays silent on valid input. The
promise is checked, never assumed.
"""

from __future__ import annotations

from .solve import (
    MAX_LENGTH,
    PAIRS,
    BracketError,
    audit,
    count_unmatched,
    is_valid,
    matched_pairs,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_LENGTH",
    "PAIRS",
    "BracketError",
    "audit",
    "count_unmatched",
    "is_valid",
    "matched_pairs",
]
