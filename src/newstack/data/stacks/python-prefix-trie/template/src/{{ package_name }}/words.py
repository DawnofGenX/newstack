"""The word gate: lowercase letters, one to sixty-four of them.

A word is whole before the trie ever sees it: empty strings, digits,
punctuation, and uppercase have no place among the letters, and the
gate says so rather than letting a half-word reach the branches.
"""

from __future__ import annotations

MAX_LENGTH = 64


class WordError(ValueError):
    """A candidate is no word at all."""


def ensure_prefix(candidate: object) -> str:
    """Return the validated stem; the empty stem asks for every word."""
    if not isinstance(candidate, str):
        raise WordError(f"not a stem: {candidate!r} is not text")
    if len(candidate) > MAX_LENGTH:
        raise WordError(f"not a stem: {len(candidate)} letters is past {MAX_LENGTH}")
    if candidate and (not candidate.isascii() or not candidate.isalpha()):
        raise WordError(f"not a stem: {candidate!r} carries a non-letter")
    if candidate != candidate.lower():
        raise WordError(f"not a stem: {candidate!r} is not lowercase")
    return candidate


def ensure_word(candidate: object) -> str:
    """Return the validated word, or refuse it by name."""
    if not isinstance(candidate, str):
        raise WordError(f"not a word: {candidate!r} is not text")
    if not candidate:
        raise WordError("not a word: the empty string")
    if len(candidate) > MAX_LENGTH:
        raise WordError(f"not a word: {len(candidate)} letters is past {MAX_LENGTH}")
    if not candidate.isascii() or not candidate.isalpha():
        raise WordError(f"not a word: {candidate!r} carries a non-letter")
    if candidate != candidate.lower():
        raise WordError(f"not a word: {candidate!r} is not lowercase")
    return candidate


def describe(word: str) -> str:
    """The display form of a word, quoted the way the CLI prints it."""
    return repr(word)
