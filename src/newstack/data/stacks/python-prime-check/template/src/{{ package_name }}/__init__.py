"""Prime check over small integers."""

from __future__ import annotations

from .solve import (
    MAX_VALUE,
    PrimeCheckError,
    audit,
    is_prime,
    next_prime,
    prime_factors,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_VALUE",
    "PrimeCheckError",
    "audit",
    "is_prime",
    "next_prime",
    "prime_factors",
]
