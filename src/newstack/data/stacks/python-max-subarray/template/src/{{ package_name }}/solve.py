"""A maximum subarray sum: the largest contiguous sum of a nonempty list of integers.

Detect phrase: the largest contiguous sum is found by carrying the running total.
"""

from __future__ import annotations

MAX_VALUES = 64
MAX_VALUE = 20

__all__ = [
    "MAX_VALUE",
    "MAX_VALUES",
    "MaxSubarrayError",
    "audit",
    "solve",
    "witness",
]


class MaxSubarrayError(ValueError):
    """An input the solver refuses."""


def _validate(values) -> list:
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise MaxSubarrayError("values must be a list or tuple")
    if len(values) == 0 or len(values) > MAX_VALUES:
        raise MaxSubarrayError(f"value count out of range: {len(values)}")
    clean = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int):
            raise MaxSubarrayError("value must be an integer")
        if abs(v) > MAX_VALUE:
            raise MaxSubarrayError(f"value out of range: {v}")
        clean.append(v)
    return clean


def solve(values) -> int:
    """Return the maximum sum of a contiguous subarray (nonempty)."""
    vs = _validate(values)
    best = vs[0]
    cur = vs[0]
    for v in vs[1:]:
        cur = v if cur + v < v else cur + v
        best = cur if cur > best else best
    return best


def witness(values) -> list:
    """Return one subarray whose sum equals solve(values)."""
    vs = _validate(values)
    best_sum = vs[0]
    best_i = 0
    best_j = 0
    cur = vs[0]
    cur_i = 0
    for j in range(1, len(vs)):
        if cur + vs[j] < vs[j]:
            cur = vs[j]
            cur_i = j
        else:
            cur = cur + vs[j]
        if cur > best_sum:
            best_sum = cur
            best_i = cur_i
            best_j = j
    return vs[best_i : best_j + 1]


def audit(values) -> list:
    """Return a list of broken invariants; empty means the solver is consistent."""
    vs = _validate(values)
    problems = []
    w = witness(vs)
    if sum(w) != solve(vs):
        problems.append("witness sum mismatch")
    if w not in [vs[i : i + len(w)] for i in range(len(vs) - len(w) + 1)]:
        problems.append("witness not contiguous")
    return problems


def demo() -> list:
    stories = [
        ("single", [5], 5),
        ("classic", [-2, 1, -3, 4, -1, 2, 1, -5, 4], 6),
        ("all negative", [-3, -2, -5], -2),
    ]
    out = []
    for title, vs, want in stories:
        got = solve(vs)
        held = got == want and audit(vs) == []
        out.append((title, got, want, held))
    return out