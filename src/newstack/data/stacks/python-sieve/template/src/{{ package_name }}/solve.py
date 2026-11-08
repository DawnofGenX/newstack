"""Sieve of Eratosthenes: composites are crossed off, primes remain.

The rule this sieve keeps, and the marker the detector looks for:
each prime crosses off its multiples starting at its square. A
sieve answers the primes up to n by crossing off multiples of each
prime starting at its square. The product is exact: on every n the
shipped corpus holds, the list equals the oracle's trial-division
list. A non-positive or oversized n is named, never sieved.
"""
from __future__ import annotations

MAX_VALUE = 99

class SieveError(ValueError):
    """An n the sieve refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise SieveError("n must be an integer")
    if n < 2:
        raise SieveError("n must be at least 2")
    if n > MAX_VALUE:
        raise SieveError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def primes_up_to(n) -> list:
    """The list of primes <= n, in ascending order."""
    n = _validate(n)
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    i = 2
    while i * i <= n:
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
        i += 1
    return [p for p in range(2, n + 1) if sieve[p]]


def is_prime(n) -> bool:
    """Whether n is prime."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise SieveError("n must be an integer")
    if n < 2:
        return False
    if n > MAX_VALUE:
        raise SieveError(f"n exceeds the ceiling {MAX_VALUE}")
    return n in primes_up_to(n)


def count_primes(n) -> int:
    """How many primes are <= n."""
    return len(primes_up_to(n))


def audit(values) -> list:
    """Name every way a sieve breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = primes_up_to(n)
        oracle = [p for p in range(2, n + 1)
                  if all(p % d for d in range(2, int(p ** 0.5) + 1))]
        if got != oracle:
            breaks.append(f"primes_up_to({n}) differs")
    return breaks


__all__ = ["MAX_VALUE", "SieveError", "audit", "count_primes", "is_prime", "primes_up_to"]
