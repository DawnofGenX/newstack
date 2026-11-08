"""Vowel counting: how many vowels a string holds.

The rule this vowel count keeps, and the marker the detector looks
for: a vowel is one of a, e, i, o, u, case-insensitive. A vowel
count answers how many vowels s holds. The product is exact: on
every s the shipped corpus holds, the result equals the oracle's
sum, and the positions agree. A non-string or oversized input is
named, never counted.
"""
from __future__ import annotations

MAX_VALUE = 99
VOWELS = frozenset("aeiouAEIOU")

class VowelCountError(ValueError):
    """An input the vowel count refuses."""

    __slots__ = ()


def _validate(s) -> str:
    if not isinstance(s, str):
        raise VowelCountError("s must be a string")
    if len(s) > MAX_VALUE:
        raise VowelCountError(f"s exceeds the ceiling {MAX_VALUE}")
    return s


def is_vowel(c) -> bool:
    """Whether c is a vowel."""
    if not isinstance(c, str) or len(c) != 1:
        raise VowelCountError("c must be a single character")
    return c in VOWELS


def count_vowels(s) -> int:
    """How many vowels s holds."""
    s = _validate(s)
    return sum(1 for c in s if c in VOWELS)


def vowel_positions(s) -> list:
    """The indices of the vowels in s."""
    s = _validate(s)
    return [i for i, c in enumerate(s) if c in VOWELS]


def audit(values) -> list:
    """Name every way a vowel count breaks its own shape; empty holds."""
    breaks: list = []
    for s in values:
        got = count_vowels(s)
        oracle = sum(1 for c in s if c in "aeiouAEIOU")
        if got != oracle:
            breaks.append(f"count_vowels({s!r}) differs")
        if vowel_positions(s) != [i for i, c in enumerate(s) if c in "aeiouAEIOU"]:
            breaks.append(f"vowel_positions({s!r}) differs")
    return breaks


__all__ = [
    "MAX_VALUE",
    "VOWELS",
    "VowelCountError",
    "audit",
    "count_vowels",
    "is_vowel",
    "vowel_positions",
]
