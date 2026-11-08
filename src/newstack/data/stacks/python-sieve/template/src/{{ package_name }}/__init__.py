"""Sieve of Eratosthenes up to small n."""

from __future__ import annotations

from .solve import (
    MAX_VALUE,
    SieveError,
    audit,
    count_primes,
    is_prime,
    primes_up_to,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_VALUE",
    "SieveError",
    "audit",
    "count_primes",
    "is_prime",
    "primes_up_to",
]
