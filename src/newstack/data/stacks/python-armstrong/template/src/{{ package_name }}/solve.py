"""Armstrong number: sum of its digits each raised to the digit count equals n.

The rule this armstrong check keeps, and the marker the detector
looks for: each digit is raised to the power of the digit count,
then summed. An armstrong number answers whether that sum equals n.
The product is exact: on every n the shipped corpus holds, the
result equals the oracle's brute sum, and the check agrees. A
negative or oversized n is named, never checked.
"""
from __future__ import annotations

MAX_VALUE = 9999

class ArmstrongError(ValueError):
    """An n the armstrong check refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise ArmstrongError("n must be an integer")
    if n < 0:
        raise ArmstrongError("n must be non-negative")
    if n > MAX_VALUE:
        raise ArmstrongError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


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


def armstrong_sum(n) -> int:
    """Sum of each digit raised to the digit count."""
    n = _validate(n)
    k = digit_count(n)
    total = 0
    m = n
    while m:
        total += (m % 10) ** k
        m //= 10
    return total


def is_armstrong(n) -> bool:
    """Whether n is an armstrong number."""
    n = _validate(n)
    return armstrong_sum(n) == n


def audit(values) -> list:
    """Name every way an armstrong check breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = is_armstrong(n)
        k = digit_count(n)
        oracle = sum(int(c) ** k for c in str(n)) == n
        if got != oracle:
            breaks.append(f"is_armstrong({n}) differs")
    return breaks


__all__ = ["MAX_VALUE", "ArmstrongError", "armstrong_sum", "audit", "digit_count", "is_armstrong"]
