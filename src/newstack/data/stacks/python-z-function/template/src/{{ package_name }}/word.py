"""The gate: lowercase words, and nothing else.

A Z-array is only as honest as the word it was cut from, so the
gate keeps uppercase, digits, spaces, and non-strings out before
any array is cut. The empty word is legal and stays honest: it owns
the empty array, and it sits at every position of any pattern.
"""

from __future__ import annotations

MAX_WORD = 1_000_000


class WordError(ValueError):
    """A candidate is no word at all."""


def _plain(value: str) -> bool:
    """Whether every character is a lowercase ASCII letter."""
    return all("a" <= ch <= "z" for ch in value)


def ensure_word(candidate: object) -> str:
    """Return the validated word; anything but lowercase letters fails."""
    if not isinstance(candidate, str):
        raise WordError(f"not a word: {candidate!r} is not a string")
    if not _plain(candidate):
        raise WordError(f"not a word: {candidate!r} is not lowercase letters")
    if len(candidate) > MAX_WORD:
        raise WordError(f"not a word: {len(candidate)} past {MAX_WORD}")
    return candidate


def ensure_pattern(candidate: object) -> str:
    """Return the validated pattern; the same gate, under its other name."""
    return ensure_word(candidate)


def describe(value: str) -> str:
    """The display form of a word, quoted so emptiness shows."""
    return repr(value)
