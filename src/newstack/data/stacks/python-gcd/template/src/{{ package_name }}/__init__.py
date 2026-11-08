"""Greatest common divisor over small integers."""

from __future__ import annotations

from .solve import (
    MAX_VALUE,
    GcdError,
    audit,
    extended_gcd,
    gcd,
    mod_inverse,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_VALUE",
    "GcdError",
    "audit",
    "extended_gcd",
    "gcd",
    "mod_inverse",
]
