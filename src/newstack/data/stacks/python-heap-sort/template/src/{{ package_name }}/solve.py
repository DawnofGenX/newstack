"""Heap sort: a heap answers the order, one sift at a time.

The rule this sorter keeps, and the marker the detector looks for:
the largest rides to the top and is peeled off last. A heap sort
answers the sorted list by building a max-heap, then repeatedly
moving the root to the end and sifting the new root down. The
product is exact: on every array the shipped corpus holds, the
sorted list equals the oracle's sorted list entry for entry. The
sort is not stable, but the output is exact, and a negative or
oversized value is named, never sorted.
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


def _sift_down(arr: list, start: int, end: int) -> None:
    root = start
    while True:
        child = 2 * root + 1
        if child > end:
            break
        if child + 1 <= end and arr[child] < arr[child + 1]:
            child += 1
        if arr[root] < arr[child]:
            arr[root], arr[child] = arr[child], arr[root]
            root = child
        else:
            break


def _sort(values: list) -> list:
    arr = list(values)
    n = len(arr)
    for start in range(n // 2 - 1, -1, -1):
        _sift_down(arr, start, n - 1)
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        _sift_down(arr, 0, end - 1)
    return arr


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
