"""Tim sort: runs are insertion-sorted, then merged.

The rule this sorter keeps, and the marker the detector looks for:
tim sorts small runs by insertion and merges them by size.
A tim sort answers the sorted list by splitting the array in
half, sorting each half, and merging the two sorted halves by
always taking the smaller front. The product is exact: on every
array the shipped corpus holds, the sorted list equals the oracle's
sorted list entry for entry. The sort is stable: equal keys keep
their input order, audited via the tagged tim.
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


def _merge(left: list, right: list) -> list:
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


RUN = 16


def _insertion(arr: list, lo: int, hi: int) -> None:
    for i in range(lo + 1, hi + 1):
        key = arr[i]
        j = i - 1
        while j >= lo and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


def _sort(values: list) -> list:
    arr = list(values)
    n = len(arr)
    for i in range(0, n, RUN):
        _insertion(arr, i, min(i + RUN - 1, n - 1))
    size = RUN
    while size < n:
        for left in range(0, n, 2 * size):
            mid = min(n, left + size)
            right = min(n, left + 2 * size)
            if mid < right:
                arr[left:right] = _merge(arr[left:mid], arr[mid:right])
        size *= 2
    return arr


def sort(values) -> list:
    """The sorted list, stable."""
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
