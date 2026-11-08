"""Anagrams: two strings that are rearrangements of each other.

The rule this anagram keeps, and the marker the detector looks for:
two strings are anagrams when their sorted letters agree. An
anagram answers whether a and b are rearrangements. The product is
exact: on every pair the shipped corpus holds, the result equals
the oracle's sorted comparison, and the signature agrees. A
non-string or oversized input is named, never compared.
"""
from __future__ import annotations

MAX_VALUE = 99

class AnagramError(ValueError):
    """An input the anagram refuses."""

    __slots__ = ()


def _validate(s) -> str:
    if not isinstance(s, str):
        raise AnagramError("s must be a string")
    if len(s) > MAX_VALUE:
        raise AnagramError(f"s exceeds the ceiling {MAX_VALUE}")
    return s


def signature(s) -> list:
    """The sorted list of characters of s."""
    s = _validate(s)
    return sorted(s)


def is_anagram(a, b) -> bool:
    """Whether a and b are anagrams."""
    a = _validate(a)
    b = _validate(b)
    return sorted(a) == sorted(b)


def audit(pairs) -> list:
    """Name every way an anagram breaks its own shape; empty holds."""
    breaks: list = []
    for a, b in pairs:
        got = is_anagram(a, b)
        oracle = sorted(a) == sorted(b)
        if got != oracle:
            breaks.append(f"is_anagram({a!r},{b!r}) differs")
        if signature(a) != sorted(a):
            breaks.append(f"signature({a!r}) differs")
    return breaks


__all__ = ["MAX_VALUE", "AnagramError", "audit", "is_anagram", "signature"]
