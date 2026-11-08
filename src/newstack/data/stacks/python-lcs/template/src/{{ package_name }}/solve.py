"""Longest common subsequence over small strings.

The rule this lcs keeps, and the marker the detector looks for:
a subsequence keeps order, drops letters. An lcs answers the longest
string that is a subsequence of both inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_LENGTH = 64


class LcsError(ValueError):
    """Raised when a request cannot be honoured."""


@dataclass(frozen=True)
class Break:
    left: str
    right: str
    reason: str


def _validate(s: str, name: str) -> str:
    if not isinstance(s, str):
        raise LcsError(f"{name} must be a str, got {type(s).__name__}")
    if len(s) > MAX_LENGTH:
        raise LcsError(f"{name} too long: {len(s)} > {MAX_LENGTH}")
    return s


def lcs_length(a: str, b: str) -> int:
    a = _validate(a, "a")
    b = _validate(b, "b")
    n, m = len(a), len(b)
    prev = [0] * (m + 1)
    for i in range(1, n + 1):
        cur = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = max(prev[j], cur[j - 1])
        prev = cur
    return prev[m]


def lcs(a: str, b: str) -> str:
    a = _validate(a, "a")
    b = _validate(b, "b")
    n, m = len(a), len(b)
    table = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    out = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif table[i - 1][j] >= table[i][j - 1]:
            i -= 1
        else:
            j -= 1
    out.reverse()
    return "".join(out)


def audit(pairs: list[tuple[str, str]]) -> list[Break]:
    breaks: list[Break] = []
    for a, b in pairs:
        try:
            got = lcs(a, b)
        except LcsError as exc:
            breaks.append(Break(a, b, str(exc)))
            continue
        if len(got) != lcs_length(a, b):
            breaks.append(Break(a, b, "length mismatch"))
            continue
        # verify subsequence property
        it = iter(b)
        if not all(ch in it for ch in got):
            breaks.append(Break(a, b, "not a subsequence of b"))
            continue
        it = iter(a)
        if not all(ch in it for ch in got):
            breaks.append(Break(a, b, "not a subsequence of a"))
    return breaks


__all__ = ["MAX_LENGTH", "Break", "LcsError", "audit", "lcs", "lcs_length"]
