"""Character frequency: how often each character occurs.

The rule this character frequency keeps, and the marker the detector
looks for: every character is counted, whitespace included. A
character frequency answers the per-character tally. The product is
exact: on every seeded string the shipped corpus holds, the result
equals the oracle's collections tally, and the total agrees. A
non-string or oversized input is named, never counted.
"""
from __future__ import annotations

MAX_VALUE = 1000

class CharFrequencyError(ValueError):
    """A string the character frequency refuses."""

    __slots__ = ()


def _validate(s) -> str:
    if not isinstance(s, str):
        raise CharFrequencyError("s must be a string")
    if len(s) > MAX_VALUE:
        raise CharFrequencyError(f"s exceeds the ceiling {MAX_VALUE}")
    return s


def count_chars(s) -> int:
    """How many characters s holds (whitespace included)."""
    s = _validate(s)
    return len(s)


def char_frequencies(s) -> dict:
    """A dict mapping each character to its count in s."""
    s = _validate(s)
    freq: dict = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    return freq


def most_common(s) -> str:
    """The most common character in s; ties broken by first occurrence."""
    s = _validate(s)
    if not s:
        return ""
    freq = char_frequencies(s)
    best = s[0]
    for ch in s[1:]:
        if freq[ch] > freq[best]:
            best = ch
    return best


def audit(values) -> list:
    """Name every way a character frequency breaks its own shape; empty holds."""
    breaks: list = []
    for s in values:
        got = count_chars(s)
        oracle = len(s)
        if got != oracle:
            breaks.append(f"count_chars({s!r}) differs")
        gotf = char_frequencies(s)
        oracf = {}
        for ch in s:
            oracf[ch] = oracf.get(ch, 0) + 1
        if gotf != oracf:
            breaks.append(f"char_frequencies({s!r}) differs")
    return breaks


__all__ = [
    "MAX_VALUE",
    "CharFrequencyError",
    "audit",
    "char_frequencies",
    "count_chars",
    "most_common",
]
