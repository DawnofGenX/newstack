"""Subset sum over small nonnegative integers.

The rule this solver keeps, and the marker the detector looks for:
a subset either sums to the target or it does not, the witness
names the chosen subset, and the audit reports any mismatch.
Mutate the boolean and a no becomes a yes.

Detect phrase: a subset either sums to the target or it does not.
"""

from __future__ import annotations

MAX_VALUES = 8
MAX_VALUE = 40
MAX_TARGET = 50

__all__ = [
    "MAX_TARGET",
    "MAX_VALUE",
    "MAX_VALUES",
    "SubsetSumError",
    "audit",
    "solve",
    "witness",
]


class SubsetSumError(ValueError):
    """An input the solver refuses."""


def _validate(values, target) -> tuple:
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise SubsetSumError("values must be a list or tuple")
    if len(values) > MAX_VALUES:
        raise SubsetSumError(f"value count out of range: {len(values)}")
    clean = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int):
            raise SubsetSumError("value must be an integer")
        if v < 0 or v > MAX_VALUE:
            raise SubsetSumError(f"value out of range: {v}")
        clean.append(v)
    if isinstance(target, bool) or not isinstance(target, int):
        raise SubsetSumError("target must be an integer")
    if target < 0 or target > MAX_TARGET:
        raise SubsetSumError(f"target out of range: {target}")
    return tuple(clean), target


def solve(values, target) -> bool:
    vs, t = _validate(values, target)
    # dp[j] reachable?
    dp = [False] * (t + 1)
    dp[0] = True
    for v in vs:
        for j in range(t, v - 1, -1):
            if dp[j - v]:
                dp[j] = True
    return dp[t]


def witness(values, target) -> list:
    vs, t = _validate(values, target)
    n = len(vs)
    if not solve(vs, t):
        return []
    # DP table for reconstruction
    dp = [[False] * (t + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        v = vs[i - 1]
        for j in range(t + 1):
            dp[i][j] = dp[i - 1][j]
            if j >= v and dp[i - 1][j - v]:
                dp[i][j] = True
    chosen = []
    j = t
    for i in range(n, 0, -1):
        if dp[i][j] and not dp[i - 1][j]:
            chosen.append(vs[i - 1])
            j -= vs[i - 1]
    chosen.reverse()
    return chosen


def audit(values, target) -> list:
    try:
        vs, t = _validate(values, target)
    except SubsetSumError as exc:
        return [str(exc)]
    got = solve(vs, t)
    errors = []
    # brute-force oracle
    n = len(vs)
    oracle = False
    for mask in range(1 << n):
        s = 0
        for i in range(n):
            if mask & (1 << i):
                s += vs[i]
        if s == t:
            oracle = True
            break
    if got != oracle:
        errors.append("answer does not match oracle")
    w = witness(vs, t)
    if got:
        if sum(w) != t:
            errors.append("witness does not sum to target")
        # subsequence check
        it = iter(vs)
        for x in w:
            while True:
                try:
                    y = next(it)
                except StopIteration:
                    errors.append("witness is not a subsequence")
                    break
                if y == x:
                    break
            if errors and errors[-1] == "witness is not a subsequence":
                break
    else:
        if w:
            errors.append("witness should be empty")
    return errors
