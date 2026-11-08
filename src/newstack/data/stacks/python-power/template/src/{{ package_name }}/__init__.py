"""Fast exponentiation over small integers."""

from __future__ import annotations

from .solve import (
    MAX_BASE,
    MAX_EXPONENT,
    Break,
    PowerError,
    audit,
    fast_pow,
    pow_mod,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_BASE",
    "MAX_EXPONENT",
    "Break",
    "PowerError",
    "audit",
    "fast_pow",
    "pow_mod",
]
