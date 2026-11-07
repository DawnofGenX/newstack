"""The pattern gate: lowercase letters, and nothing else.

A scanner is only as honest as the strings it is fed, so the gate
keeps uppercase, digits, spaces, and non-strings out before any
window is hashed. The empty pattern is legal and stays honest: it
matches at every position of any text.
"""

from __future__ import annotations

MAX_PATTERN = 4096
MAX_TEXT = 1_000_000


class PatternError(ValueError):
    """A candidate is no pattern at all."""


def _plain(value: str) -> bool:
    """Whether every character is a lowercase ASCII letter."""
    return all("a" <= ch <= "z" for ch in value)


def ensure_pattern(candidate: object) -> str:
    """Return the validated pattern; anything but lowercase letters fails."""
    if not isinstance(candidate, str):
        raise PatternError(f"not a pattern: {candidate!r} is not a string")
    if not _plain(candidate):
        raise PatternError(f"not a pattern: {candidate!r} is not lowercase letters")
    if len(candidate) > MAX_PATTERN:
        raise PatternError(f"not a pattern: {len(candidate)} past {MAX_PATTERN}")
    return candidate


def ensure_text(candidate: object) -> str:
    """Return the validated text; anything but lowercase prose fails."""
    if not isinstance(candidate, str):
        raise PatternError(f"not a text: {candidate!r} is not a string")
    if not _plain(candidate):
        raise PatternError(f"not a text: {candidate!r} is not lowercase letters")
    if len(candidate) > MAX_TEXT:
        raise PatternError(f"not a text: {len(candidate)} past {MAX_TEXT}")
    return candidate


def describe(value: str) -> str:
    """The display form of a pattern, quoted so emptiness shows."""
    return repr(value)
