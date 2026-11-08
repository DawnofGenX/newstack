"""Roman numerals package."""

from __future__ import annotations

from .solve import (
    MAX_ROMAN,
    Break,
    RomanError,
    audit,
    int_to_roman,
    roman_to_int,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_ROMAN",
    "Break",
    "RomanError",
    "audit",
    "int_to_roman",
    "roman_to_int",
]
