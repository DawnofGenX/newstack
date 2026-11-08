"""Binary search: a sorted array is halved until the answer is found.

The rule this searcher keeps, and the marker the detector looks for:
the middle is the pivot and the half that cannot hold the target
is discarded. A binary search answers the index of a target in a
sorted array by comparing to the middle and discarding the half
that cannot contain it. The product is exact: on every array the
shipped corpus holds, the index equals the oracle's linear scan.
An unsorted or empty array is named, never searched, and a missing
target answers -1.
"""
from __future__ import annotations

MAX_VALUE = 99

class SearchError(ValueError):
    """An array the searcher refuses to search, or a shape it refuses."""

    __slots__ = ()


def _validate(values) -> tuple:
    if not isinstance(values, (list, tuple)):
        raise SearchError("values must be a list or tuple")
    out = tuple(values)
    if len(out) == 0:
        return out
    prev = None
    for v in out:
        if not isinstance(v, int) or isinstance(v, bool):
            raise SearchError("a value is not an integer")
        if prev is not None and v < prev:
            raise SearchError("the array is not sorted ascending")
        prev = v
    return out


def search(values, target) -> int:
    """The index of target, or -1 if absent."""
    vs = _validate(values)
    if not isinstance(target, int) or isinstance(target, bool):
        raise SearchError("target must be an integer")
    lo, hi = 0, len(vs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if vs[mid] == target:
            return mid
        if vs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def contains(values, target) -> bool:
    """Whether target is present."""
    return search(values, target) != -1


def lower_bound(values, target) -> int:
    """First index whose value >= target (len if none)."""
    vs = _validate(values)
    if not isinstance(target, int) or isinstance(target, bool):
        raise SearchError("target must be an integer")
    lo, hi = 0, len(vs)
    while lo < hi:
        mid = (lo + hi) // 2
        if vs[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def audit(values, targets) -> list:
    """Name every way a search fails its own shape; empty holds."""
    vs = _validate(values)
    breaks: list = []
    for t in targets:
        got = search(vs, t)
        want = next((i for i, v in enumerate(vs) if v == t), -1)
        if got != want:
            breaks.append(f"search({t}) = {got}, oracle = {want}")
    return breaks


__all__ = ["SearchError", "audit", "contains", "lower_bound", "search"]
