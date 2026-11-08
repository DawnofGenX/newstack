"""Digit sum: the sum of the decimal digits of n.

The rule this digit sum keeps, and the marker the detector looks
for: each decimal digit is peeled off and added. A digit sum
answers the sum of the decimal digits of n. The product is exact:
on every n the shipped corpus holds, the result equals the oracle's
string sum, and the product agrees. A negative or oversized n is
named, never summed.
"""
from __future__ import annotations

MAX_VALUE = 9999

class DigitSumError(ValueError):
    """An n the digit sum refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise DigitSumError("n must be an integer")
    if n < 0:
        raise DigitSumError("n must be non-negative")
    if n > MAX_VALUE:
        raise DigitSumError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def digit_sum(n) -> int:
    """The sum of the decimal digits of n."""
    n = _validate(n)
    total = 0
    while n:
        total += n % 10
        n //= 10
    return total


def digit_product(n) -> int:
    """The product of the decimal digits of n."""
    n = _validate(n)
    if n == 0:
        return 0
    total = 1
    while n:
        total *= n % 10
        n //= 10
    return total


def digit_count(n) -> int:
    """How many decimal digits n has."""
    n = _validate(n)
    if n == 0:
        return 1
    count = 0
    while n:
        count += 1
        n //= 10
    return count


def audit(values) -> list:
    """Name every way a digit sum breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = digit_sum(n)
        oracle = sum(int(c) for c in str(n))
        if got != oracle:
            breaks.append(f"digit_sum({n}) differs")
    return breaks


__all__ = ["MAX_VALUE", "DigitSumError", "audit", "digit_count", "digit_product", "digit_sum"]
