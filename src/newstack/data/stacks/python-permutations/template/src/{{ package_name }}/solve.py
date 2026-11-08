"""Permutations: every ordering of a small list of items.

The rule this generator keeps, and the marker the detector looks for:
a permutation keeps every item exactly once, in a new order. The
permutations of a list are produced by choosing each item in turn
as the first element, then permuting the rest. The product is
exact: on every list the shipped corpus holds, the count equals the
factorial of the length and every entry is a true permutation.
Permute more than the ceiling or a non-list input and it refuses
loudly; a permutation keeps every item exactly once, in a new order.
"""
from __future__ import annotations

import math

MAX_N = 8


class PermutationError(ValueError):
    """An input the generator refuses to permute."""

    __slots__ = ()


def _validate(items) -> tuple:
    if not isinstance(items, (list, tuple)):
        raise PermutationError("items must be a list or tuple")
    out = tuple(items)
    if len(out) > MAX_N:
        raise PermutationError(f"too many items: {len(out)} > {MAX_N}")
    return out


def permutations(items) -> list:
    """Every ordering of items, as a list of tuples."""
    vs = _validate(items)
    if not vs:
        return [()]
    out: list = []
    for i, v in enumerate(vs):
        rest = vs[:i] + vs[i + 1:]
        for p in permutations(rest):
            out.append((v, *p))
    return out


def count(n) -> int:
    """Factorial of n: how many permutations of n distinct items."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise PermutationError("n must be an integer")
    if n < 0:
        raise PermutationError("n must be non-negative")
    if n > MAX_N:
        raise PermutationError(f"n exceeds the ceiling {MAX_N}")
    return math.factorial(n)


def unique(items) -> list:
    """Distinct permutations only, in sorted order."""
    vs = _validate(items)
    seen = set()
    out = []
    for p in permutations(vs):
        if p not in seen:
            seen.add(p)
            out.append(p)
    return sorted(out)


def audit(items) -> list:
    """Name every way a permutation set fails its own shape; empty holds."""
    vs = _validate(items)
    breaks: list = []
    got = permutations(vs)
    for p in got:
        if sorted(p) != sorted(vs):
            breaks.append("an entry is not a permutation")
            break
    if len(set(vs)) == len(vs) and len(got) != math.factorial(len(vs)):
        breaks.append("count differs from factorial")
    return breaks


__all__ = ["MAX_N", "PermutationError", "audit", "count", "permutations", "unique"]
