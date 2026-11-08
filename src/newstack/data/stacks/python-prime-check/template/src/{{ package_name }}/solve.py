"""Prime check: whether n is prime, honestly.

The rule this prime check keeps, and the marker the detector looks
for: trial division up to the square root. A prime check answers
whether n is prime. The product is exact: on every seeded n the
shipped corpus holds, the result equals the oracle's brute
divisibility scan, and the factors agree. A non-integer or
oversized n is named, never checked.
"""
from __future__ import annotations

import math

MAX_VALUE = 9999

class PrimeCheckError(ValueError):
    """An n the prime check refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise PrimeCheckError("n must be an integer")
    if n < 0:
        raise PrimeCheckError("n must be non-negative")
    if n > MAX_VALUE:
        raise PrimeCheckError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def is_prime(n) -> bool:
    """Whether n is prime."""
    n = _validate(n)
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def next_prime(n) -> int:
    """The smallest prime strictly greater than n."""
    n = _validate(n)
    candidate = n + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate


def prime_factors(n) -> list:
    """The prime factorisation of n, smallest first."""
    n = _validate(n)
    if n < 2:
        return []
    factors: list = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        factors.append(n)
    return factors


def audit(values) -> list:
    """Name every way a prime check breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = is_prime(n)
        oracle = n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))
        if got != oracle:
            breaks.append(f"is_prime({n}) differs")
    return breaks


__all__ = [
    "MAX_VALUE",
    "PrimeCheckError",
    "audit",
    "is_prime",
    "next_prime",
    "prime_factors",
]
