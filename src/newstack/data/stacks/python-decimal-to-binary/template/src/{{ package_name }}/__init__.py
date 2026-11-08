"""Decimal to binary conversion over small nonnegative integers."""

from __future__ import annotations

from .solve import (
    MAX_DECIMAL,
    Break,
    ConversionError,
    audit,
    binary_to_decimal,
    dec_to_binary,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_DECIMAL",
    "Break",
    "ConversionError",
    "audit",
    "binary_to_decimal",
    "dec_to_binary",
]