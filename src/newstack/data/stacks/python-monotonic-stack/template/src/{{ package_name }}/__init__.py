"""Monotonic stack package."""

from .solve import (
    MAX_LEN,
    MonotonicError,
    audit,
    next_greater,
    next_smaller,
    previous_greater,
)

__all__ = [
    "MAX_LEN",
    "MonotonicError",
    "audit",
    "next_greater",
    "next_smaller",
    "previous_greater",
]
