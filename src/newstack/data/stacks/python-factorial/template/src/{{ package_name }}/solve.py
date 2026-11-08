"""Factorial: n! by multiplying the integers in order.

The rule this factorial keeps, and the marker the detector looks for:
the product grows by one factor at a time, from 1 up to n. A
factorial answers n! by multiplying the integers from 1 to n. The
product is exact: on every n the shipped corpus holds, the result
equals the oracle's sequential product, and binomial follows. A
negative or oversized n is named, never multiplied.
"""
from __future__ import annotations

MAX_VALUE = 20

class FactorialError(ValueError):
    """An n the factorial refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise FactorialError("n must be an integer")
    if n < 0:
        raise FactorialError("n must be non-negative")
    if n > MAX_VALUE:
        raise FactorialError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def factorial(n) -> int:
    """n!."""
    n = _validate(n)
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def binomial(n, k) -> int:
    """C(n, k) = n! / (k! (n-k)!)."""
    n = _validate(n)
    if not isinstance(k, int) or isinstance(k, bool):
        raise FactorialError("k must be an integer")
    if k < 0 or k > n:
        raise FactorialError("k out of range")
    return factorial(n) // (factorial(k) * factorial(n - k))


def audit(values) -> list:
    """Name every way a factorial breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = factorial(n)
        oracle = 1
        for i in range(2, n + 1):
            oracle *= i
        if got != oracle:
            breaks.append(f"factorial({n}) differs")
    return breaks


__all__ = ["MAX_VALUE", "FactorialError", "audit", "binomial", "factorial"]
