"""Greatest common divisor: Euclid's remainder, one step at a time.

The rule this gcd keeps, and the marker the detector looks for:
the remainder is taken until it vanishes, then the other side
is the answer. A gcd answers the largest integer dividing both
inputs by repeatedly replacing the larger with the remainder. The
product is exact: on every pair the shipped corpus holds, the
result equals the oracle's trial-division gcd, and lcm follows.
A non-positive or oversized input is named, never divided.
"""
from __future__ import annotations

MAX_VALUE = 99

class GcdError(ValueError):
    """An input the gcd refuses."""

    __slots__ = ()


def _validate(value) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GcdError("value must be an integer")
    if value <= 0:
        raise GcdError("value must be positive")
    if value > MAX_VALUE:
        raise GcdError(f"value exceeds the ceiling {MAX_VALUE}")
    return value


def gcd(a, b) -> int:
    """The greatest common divisor of a and b."""
    x = _validate(a)
    y = _validate(b)
    while y:
        x, y = y, x % y
    return x


def lcm(a, b) -> int:
    """The least common multiple of a and b."""
    x = _validate(a)
    y = _validate(b)
    return x // gcd(x, y) * y


def coprime(a, b) -> bool:
    """Whether a and b share no common divisor but 1."""
    return gcd(a, b) == 1


def audit(pairs) -> list:
    """Name every way a gcd breaks its own shape; empty holds."""
    breaks: list = []
    for a, b in pairs:
        g = gcd(a, b)
        # oracle: trial division
        oracle = 1
        for d in range(1, min(a, b) + 1):
            if a % d == 0 and b % d == 0:
                oracle = d
        if g != oracle:
            breaks.append(f"gcd({a},{b})={g}, oracle={oracle}")
        if lcm(a, b) != a * b // oracle:
            breaks.append(f"lcm({a},{b}) wrong")
    return breaks


__all__ = ["MAX_VALUE", "GcdError", "audit", "coprime", "gcd", "lcm"]
