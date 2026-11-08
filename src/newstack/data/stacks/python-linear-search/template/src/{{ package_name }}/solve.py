"""Linear search: the array is walked until the target is found.

The rule this searcher keeps, and the marker the detector looks for:
the first match wins and the walk stops there. A linear search
answers the index of a target by walking the array from the front
and stopping at the first match. The product is exact: on every
array the shipped corpus holds, the index equals the oracle's
first-match scan. An empty array answers -1, and a missing target
answers -1.
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
    for v in out:
        if not isinstance(v, int) or isinstance(v, bool):
            raise SearchError("a value is not an integer")
        if v < 0 or v > MAX_VALUE:
            raise SearchError("a value is out of range")
    return out


def search(values, target) -> int:
    """The first index of target, or -1 if absent."""
    vs = _validate(values)
    if not isinstance(target, int) or isinstance(target, bool):
        raise SearchError("target must be an integer")
    if target < 0 or target > MAX_VALUE:
        raise SearchError("target is out of range")
    for i, v in enumerate(vs):
        if v == target:
            return i
    return -1


def contains(values, target) -> bool:
    """Whether target is present."""
    return search(values, target) != -1


def count(values, target) -> int:
    """How many times target appears."""
    vs = _validate(values)
    if not isinstance(target, int) or isinstance(target, bool):
        raise SearchError("target must be an integer")
    return sum(1 for v in vs if v == target)


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


__all__ = ["MAX_VALUE", "SearchError", "audit", "contains", "count", "search"]
