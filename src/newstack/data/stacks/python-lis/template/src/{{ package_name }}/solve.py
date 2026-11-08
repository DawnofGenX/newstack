"""Longest strictly increasing subsequence of a small integer list.

The rule this solver keeps, and the marker the detector looks for:
the longest chain is built one survivor at a time, the witness
names the chosen subsequence, and the audit reports any shorter
chain. Mutate the comparison and equal values sneak in.

Detect phrase: the longest chain is built one survivor at a time.
"""

from __future__ import annotations

MAX_VALUES = 8
MAX_VALUE = 200

__all__ = [
    "MAX_VALUE",
    "MAX_VALUES",
    "LISError",
    "audit",
    "solve",
    "witness",
]


class LISError(ValueError):
    """An input the solver refuses."""


def _validate(values) -> tuple:
    if isinstance(values, str) or not isinstance(values, (list, tuple)):
        raise LISError("values must be a list or tuple")
    if len(values) == 0 or len(values) > MAX_VALUES:
        raise LISError(f"value count out of range: {len(values)}")
    clean = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int):
            raise LISError("value must be an integer")
        if v < 0 or v > MAX_VALUE:
            raise LISError(f"value out of range: {v}")
        clean.append(v)
    return tuple(clean)


def solve(values) -> int:
    vs = _validate(values)
    n = len(vs)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if vs[j] < vs[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
    return max(dp) if n else 0


def witness(values) -> list:
    vs = _validate(values)
    n = len(vs)
    dp = [1] * n
    parent = [-1] * n
    for i in range(1, n):
        for j in range(i):
            if vs[j] < vs[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                parent[i] = j
    if n == 0:
        return []
    idx = max(range(n), key=lambda i: dp[i])
    out = []
    while idx != -1:
        out.append(vs[idx])
        idx = parent[idx]
    out.reverse()
    return out


def audit(values) -> list:
    try:
        vs = _validate(values)
    except LISError as exc:
        return [str(exc)]
    got = solve(vs)
    errors = []
    # brute-force subset enumeration oracle
    n = len(vs)
    best = 0
    for mask in range(1 << n):
        seq = [vs[i] for i in range(n) if mask & (1 << i)]
        if all(seq[k] < seq[k + 1] for k in range(len(seq) - 1)):
            best = max(best, len(seq))
    if got != best:
        errors.append("answer does not match oracle")
    w = witness(vs)
    if got != 0:
        if len(w) != got:
            errors.append("witness length does not match answer")
        if not all(w[k] < w[k + 1] for k in range(len(w) - 1)):
            errors.append("witness is not increasing")
        # witness must be a subsequence
        it = iter(vs)
        if not all(x in it for x in w):
            # fallback: positional check
            pos = 0
            for x in w:
                while pos < n and vs[pos] != x:
                    pos += 1
                if pos >= n:
                    errors.append("witness is not a subsequence")
                    break
                pos += 1
    else:
        if w:
            errors.append("witness should be empty")
    return errors
