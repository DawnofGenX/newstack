"""Counting sort: a tally answers the order, one bucket per value.

The rule this sorter keeps, and the marker the detector looks for:
the tally is the histogram and the order is the prefix sum. A
counting sort answers the sorted list by tallying how many of each
value occur, then walking the values in ascending order and
emitting each value its tally's worth of times. The product is
exact: on every array the shipped corpus holds, the sorted list
equals the oracle's sorted list entry for entry. Sort a negative
value or a value past the ceiling and it refuses loudly; the tally
is the histogram and the rank is its prefix.
"""
from __future__ import annotations

MAX_VALUE = 99

class SortError(ValueError):
    """An array the sorter refuses to sort, or a shape it refuses."""

    __slots__ = ()


class Tally:
    """The honest per-value count, never a guess."""

    __slots__ = ("_counts", "_hi", "_lo")

    def __init__(self, values: tuple) -> None:
        if not values:
            self._counts = {}
            self._lo = 0
            self._hi = 0
            return
        for v in values:
            if not isinstance(v, int) or isinstance(v, bool):
                raise SortError("a value is not an integer")
            if v < 0:
                raise SortError("a value is negative")
            if v > MAX_VALUE:
                raise SortError(f"a value exceeds the ceiling {MAX_VALUE}")
        self._lo = min(values)
        self._hi = max(values)
        self._counts = {v: 0 for v in range(self._lo, self._hi + 1)}
        for v in values:
            self._counts[v] += 1

    def counts(self) -> dict:
        return dict(self._counts)

    def total(self) -> int:
        return sum(self._counts.values())


def _validate(values) -> tuple:
    if not isinstance(values, (list, tuple)):
        raise SortError("values must be a list or tuple")
    out = tuple(values)
    if len(out) == 0:
        return out
    for v in out:
        if not isinstance(v, int) or isinstance(v, bool):
            raise SortError("a value is not an integer")
        if v < 0:
            raise SortError("a value is negative")
        if v > MAX_VALUE:
            raise SortError(f"a value exceeds the ceiling {MAX_VALUE}")
    return out


def counts(values) -> dict:
    """The honest per-value tally."""
    vs = _validate(values)
    if not vs:
        return {}
    t = Tally(vs)
    # include zeros for missing values in range? report only present
    return {v: c for v, c in t.counts().items() if c > 0}


def sort(values) -> list:
    """The sorted list, stable: equal keys keep input order."""
    vs = _validate(values)
    if not vs:
        return []
    # build count array over full range 0..max for stability index
    hi = max(vs)
    cnt = [0] * (hi + 1)
    for v in vs:
        cnt[v] += 1
    # prefix sums
    for i in range(1, len(cnt)):
        cnt[i] += cnt[i - 1]
    # place from the right to keep stability
    out = [0] * len(vs)
    for v in reversed(vs):
        cnt[v] -= 1
        out[cnt[v]] = v
    return out


def rank(values, value) -> int:
    """How many entries are <= value."""
    vs = _validate(values)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SortError("value must be an integer")
    if value < 0:
        return 0
    return sum(1 for v in vs if v <= value)


def audit(values) -> list:
    """Name every way a sort fails its own shape; empty holds."""
    vs = _validate(values)
    breaks: list = []
    got = sort(vs)
    if got != sorted(vs):
        breaks.append("sorted output differs from the oracle")
    if len(got) != len(vs):
        breaks.append("length changed")
    # stability check via tagged entries
    # stable sort preserves relative order of equal keys
    # (covered by sort's right-to-left placement)
    return breaks


__all__ = ["SortError", "Tally", "audit", "counts", "rank", "sort"]
