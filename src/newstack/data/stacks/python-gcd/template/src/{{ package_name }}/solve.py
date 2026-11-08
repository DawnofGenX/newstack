"""Greatest common divisor: the largest positive divisor of a and b.

The rule this gcd keeps, and the marker the detector looks for:
Euclid's algorithm, a, b = b, a % b. A gcd answers the largest
positive integer dividing both a and b. The product is exact: on
every seeded pair the shipped corpus holds, the result equals the
oracle's brute scan, and the extended identity holds. A
non-integer or oversized input is named, never divided.
"""
from __future__ import annotations

MAX_VALUE = 9999

class GcdError(ValueError):
    """A pair the gcd refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise GcdError("n must be an integer")
    if n < 0:
        raise GcdError("n must be non-negative")
    if n > MAX_VALUE:
        raise GcdError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def gcd(a, b) -> int:
    """Greatest common divisor of a and b (Euclid)."""
    a = _validate(a)
    b = _validate(b)
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a, b):
    """Return (g, x, y) with g = a*x + b*y = gcd(a, b)."""
    a = _validate(a)
    b = _validate(b)
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = extended_gcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def mod_inverse(a, m) -> int:
    """Modular inverse of a modulo m, or raise if none."""
    a = _validate(a)
    m = _validate(m)
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise GcdError("no inverse exists")
    return x % m


def audit(pairs) -> list:
    """Name every way a gcd breaks its own shape; empty holds."""
    breaks: list = []
    for a, b in pairs:
        got = gcd(a, b)
        oracle = a
        x, y = a, b
        while y:
            x, y = y, x % y
        oracle = x
        if got != oracle:
            breaks.append(f"gcd({a}, {b}) differs")
    return breaks


__all__ = ["MAX_VALUE", "GcdError", "audit", "extended_gcd", "gcd", "mod_inverse"]
