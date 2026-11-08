"""Longest common substring of two small strings.

Detect phrase: the longest shared run is grown one matching letter at a time.
"""

from __future__ import annotations

MAX_LEN = 20

__all__ = [
    "MAX_LEN",
    "LongestCommonSubstringError",
    "audit",
    "solve",
    "witness",
]


class LongestCommonSubstringError(ValueError):
    """An input the solver refuses."""


def _validate(text) -> str:
    if not isinstance(text, str):
        raise LongestCommonSubstringError("text must be a str")
    if len(text) == 0 or len(text) > MAX_LEN:
        raise LongestCommonSubstringError(f"text length out of range: {len(text)}")
    return text


def solve(a, b) -> int:
    """Return the length of the longest common substring of a and b."""
    a = _validate(a)
    b = _validate(b)
    best = 0
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            if k > best:
                best = k
    return best


def witness(a, b) -> str:
    """Return one longest common substring (empty if none)."""
    a = _validate(a)
    b = _validate(b)
    best = ""
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            if k > len(best):
                best = a[i : i + k]
    return best


def audit(a, b) -> list:
    """Return a list of broken invariants; empty means the solver is consistent."""
    a = _validate(a)
    b = _validate(b)
    problems = []
    w = witness(a, b)
    if len(w) != solve(a, b):
        problems.append("witness length mismatch")
    if w and w not in a:
        problems.append("witness not in a")
    if w and w not in b:
        problems.append("witness not in b")
    return problems


def demo() -> list:
    cases = [
        ("classic", "abcde", "xabcy", 2),
        ("none", "abc", "xyz", 0),
        ("full", "abc", "abc", 3),
    ]
    out = []
    for title, a, b, want in cases:
        got = solve(a, b)
        held = got == want and audit(a, b) == []
        out.append((title, got, want, held))
    return out