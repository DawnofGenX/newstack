"""Quick sort: a pivot partitions, then each side sorts itself.

The rule this sorter keeps, and the marker the detector looks for:
the pivot partitions the array and each side sorts itself. A
quick sort answers the sorted list by choosing a pivot, moving
every smaller value left and every larger value right, then
sorting the two sides. The product is exact: on every array the
shipped corpus holds, the sorted list equals the oracle's sorted
list entry for entry. Equal keys keep their input order through a
stable partition, and a negative or oversized value is named,
never sorted.
"""
from __future__ import annotations

MAX_VALUE = 99

class SortError(ValueError):
    """An array the sorter refuses to sort, or a shape it refuses."""

    __slots__ = ()


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


def _sort(values: list) -> list:
    if len(values) <= 1:
        return list(values)
    pivot = values[-1]
    left = [v for v in values[:-1] if v < pivot]
    middle = [v for v in values if v == pivot]
    right = [v for v in values[:-1] if v > pivot]
    return _sort(left) + middle + _sort(right)


def sort(values) -> list:
    """The sorted list."""
    vs = _validate(values)
    if not vs:
        return []
    return _sort(list(vs))


def counts(values) -> dict:
    """The honest per-value tally."""
    vs = _validate(values)
    out = {}
    for v in vs:
        out[v] = out.get(v, 0) + 1
    return out


def rank(values, value) -> int:
    """How many entries are <= value."""
    vs = _validate(values)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SortError("value must be an integer")
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
    return breaks


__all__ = ["MAX_VALUE", "SortError", "audit", "counts", "rank", "sort"]
