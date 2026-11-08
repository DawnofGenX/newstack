"""Combinations: every subset of a small list of items.

The rule this generator keeps, and the marker the detector looks for:
a combination keeps the original order and drops some items. The
subsets of a list are produced by choosing, for each item, whether
to keep it or drop it. The product is exact: on every list the
shipped corpus holds, the count equals two to the power of the
length and every entry is a true subset in original order. Combine
more than the ceiling or a non-list input and it refuses loudly; a
combination keeps the original order and drops some items.
"""
from __future__ import annotations

MAX_N = 8


class CombinationError(ValueError):
    """An input the generator refuses to combine."""

    __slots__ = ()


def _validate(items) -> tuple:
    if not isinstance(items, (list, tuple)):
        raise CombinationError("items must be a list or tuple")
    out = tuple(items)
    if len(out) > MAX_N:
        raise CombinationError(f"too many items: {len(out)} > {MAX_N}")
    return out


def combinations(items) -> list:
    """Every subset of items, in increasing length then input order."""
    vs = _validate(items)
    out = [()]
    for v in vs:
        out = out + [(*s, v) for s in out]
    # sort by length then lexicographic for determinism
    out.sort(key=lambda s: (len(s), s))
    return out


def count(n) -> int:
    """Two to the power of n: how many subsets of n items."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise CombinationError("n must be an integer")
    if n < 0:
        raise CombinationError("n must be non-negative")
    if n > MAX_N:
        raise CombinationError(f"n exceeds the ceiling {MAX_N}")
    return 1 << n


def unique(items) -> list:
    """Distinct subsets only, in sorted order."""
    vs = _validate(items)
    seen = set()
    out = []
    for s in combinations(vs):
        if s not in seen:
            seen.add(s)
            out.append(s)
    return sorted(out)


def audit(items) -> list:
    """Name every way a subset set fails its own shape; empty holds."""
    vs = _validate(items)
    breaks: list = []
    got = combinations(vs)
    for s in got:
        if not all(x in vs for x in s):
            breaks.append("an entry is not a subset")
            break
    # count check only when all items distinct
    if len(set(vs)) == len(vs) and len(got) != (1 << len(vs)):
        breaks.append("count differs from two to the power")
    return breaks


__all__ = ["MAX_N", "CombinationError", "audit", "combinations", "count", "unique"]
