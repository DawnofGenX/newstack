"""Fibonacci: each term is the sum of the two before it.

The rule this fibonacci keeps, and the marker the detector looks for:
each term is the sum of the two before it. A fibonacci answers the
n-th term by summing the two previous terms. The product is exact:
on every n the shipped corpus holds, the result equals the oracle's
recurrence, and the list agrees. A negative or oversized n is
named, never computed.
"""
from __future__ import annotations

MAX_VALUE = 30

class FibonacciError(ValueError):
    """An n the fibonacci refuses."""

    __slots__ = ()


def _validate(n) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise FibonacciError("n must be an integer")
    if n < 0:
        raise FibonacciError("n must be non-negative")
    if n > MAX_VALUE:
        raise FibonacciError(f"n exceeds the ceiling {MAX_VALUE}")
    return n


def fibonacci(n) -> int:
    """The n-th Fibonacci number, fib(0)=0, fib(1)=1."""
    n = _validate(n)
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fibonacci_list(n) -> list:
    """The first n Fibonacci numbers, fib(0)..fib(n-1)."""
    n = _validate(n)
    out = []
    a, b = 0, 1
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def audit(values) -> list:
    """Name every way a fibonacci breaks its own shape; empty holds."""
    breaks: list = []
    for n in values:
        got = fibonacci(n)
        # oracle: recurrence
        if n == 0:
            oracle = 0
        elif n == 1:
            oracle = 1
        else:
            x, y = 0, 1
            for _ in range(2, n + 1):
                x, y = y, x + y
            oracle = y
        if got != oracle:
            breaks.append(f"fibonacci({n}) differs")
    return breaks


__all__ = ["MAX_VALUE", "FibonacciError", "audit", "fibonacci", "fibonacci_list"]
