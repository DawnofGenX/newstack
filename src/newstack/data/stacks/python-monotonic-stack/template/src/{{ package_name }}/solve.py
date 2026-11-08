"""Monotonic stack algorithms over small integer lists.

a monotonic stack pops while the new value breaks the order
"""

from __future__ import annotations

MAX_LEN = 64


class MonotonicError(ValueError):
    """Raised when an input is not a valid small list."""


def _validate(values: object) -> tuple[int, ...]:
    if not isinstance(values, (list, tuple)):
        raise MonotonicError("values must be a list or tuple")
    vs = tuple(int(v) for v in values)
    if len(vs) > MAX_LEN:
        raise MonotonicError(f"list length must be <= {MAX_LEN}")
    return vs


def next_greater(values: object) -> list[int | None]:
    """Return next greater element for each index, or None."""
    vs = _validate(values)
    n = len(vs)
    result: list[int | None] = [None] * n
    stack: list[int] = []
    for i in range(n):
        while stack and vs[i] > vs[stack[-1]]:
            result[stack.pop()] = vs[i]
        stack.append(i)
    return result


def next_smaller(values: object) -> list[int | None]:
    """Return next smaller element for each index, or None."""
    vs = _validate(values)
    n = len(vs)
    result: list[int | None] = [None] * n
    stack: list[int] = []
    for i in range(n):
        while stack and vs[i] < vs[stack[-1]]:
            result[stack.pop()] = vs[i]
        stack.append(i)
    return result


def previous_greater(values: object) -> list[int | None]:
    """Return previous greater element for each index, or None."""
    vs = _validate(values)
    n = len(vs)
    result: list[int | None] = [None] * n
    stack: list[int] = []
    for i in range(n):
        while stack and vs[stack[-1]] <= vs[i]:
            stack.pop()
        result[i] = vs[stack[-1]] if stack else None
        stack.append(i)
    return result


def audit(values: object) -> dict[str, object]:
    """Report basic monotonic-stack facts."""
    vs = _validate(values)
    ng = next_greater(vs)
    ns = next_smaller(vs)
    pg = previous_greater(vs)
    return {
        "length": len(vs),
        "next_greater_count": sum(1 for x in ng if x is not None),
        "next_smaller_count": sum(1 for x in ns if x is not None),
        "previous_greater_count": sum(1 for x in pg if x is not None),
        "ok": True,
    }


__all__ = [
    "MAX_LEN",
    "MonotonicError",
    "audit",
    "next_greater",
    "next_smaller",
    "previous_greater",
]
