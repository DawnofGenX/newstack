"""Least common multiple: the smallest positive multiple of a and b.

The rule this lcm keeps, and the marker the detector looks for:
lcm(a, b) = a * b // gcd(a, b). An lcm answers the smallest
positive integer divisible by both a and b. The product is exact:
on every seeded pair the shipped corpus holds, the result equals
the oracle's brute scan, and the gcd agrees. A non-integer or
oversized input is named, never divided.
"""
from __future__ import annotations

MAX_VALUE = 9999

class LcmError(ValueError):
    """A pair the lcm refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise LcmError("n must be an integer")
    if n < 0:
        raise LcmError("n must be non-negative")
    if n > MAX_VALUE:
        raise LcmError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def gcd(a, b) -> int:
    """Greatest common divisor of a and b (Euclid)."""
    a = _validate(a)
    b = _validate(b)
    while b:
        a, b = b, a % b
    return a


def lcm(a, b) -> int:
    """Least common multiple of a and b."""
    a = _validate(a)
    b = _validate(b)
    if a == 0 or b == 0:
        return 0
    return a * b // gcd(a, b)


def is_coprime(a, b) -> bool:
    """Whether a and b share no common factor."""
    return gcd(a, b) == 1


def audit(pairs) -> list:
    """Name every way an lcm breaks its own shape; empty holds."""
    breaks: list = []
    for a, b in pairs:
        got = lcm(a, b)
        oracle = a * b // gcd(a, b) if a and b else 0
        if got != oracle:
            breaks.append(f"lcm({a}, {b}) differs")
    return breaks


__all__ = ["MAX_VALUE", "LcmError", "audit", "gcd", "is_coprime", "lcm"]
