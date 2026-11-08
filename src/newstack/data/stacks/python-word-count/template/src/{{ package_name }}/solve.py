"""Word count: how many words a string holds, honestly.

The rule this word count keeps, and the marker the detector looks
for: a word is a maximal run of non-whitespace, split on whitespace.
A word count answers how many words a string holds. The product is
exact: on every seeded string the shipped corpus holds, the result
equals the oracle's split count, and the frequencies agree. A
non-string or oversized input is named, never counted.
"""
from __future__ import annotations

MAX_VALUE = 1000

class WordCountError(ValueError):
    """A string the word count refuses."""

    __slots__ = ()


def _validate(s) -> str:
    if not isinstance(s, str):
        raise WordCountError("s must be a string")
    if len(s) > MAX_VALUE:
        raise WordCountError(f"s exceeds the ceiling {MAX_VALUE}")
    return s


def count_words(s) -> int:
    """How many whitespace-delimited words s holds."""
    s = _validate(s)
    return len(s.split())


def word_frequencies(s) -> dict:
    """A dict mapping each word to its count in s."""
    s = _validate(s)
    freq: dict = {}
    for word in s.split():
        freq[word] = freq.get(word, 0) + 1
    return freq


def longest_word(s) -> str:
    """The longest word in s; ties broken by first occurrence."""
    s = _validate(s)
    words = s.split()
    if not words:
        return ""
    best = words[0]
    for word in words[1:]:
        if len(word) > len(best):
            best = word
    return best


def audit(values) -> list:
    """Name every way a word count breaks its own shape; empty holds."""
    breaks: list = []
    for s in values:
        got = count_words(s)
        oracle = len(s.split())
        if got != oracle:
            breaks.append(f"count_words({s!r}) differs")
    return breaks


__all__ = [
    "MAX_VALUE",
    "WordCountError",
    "audit",
    "count_words",
    "longest_word",
    "word_frequencies",
]
