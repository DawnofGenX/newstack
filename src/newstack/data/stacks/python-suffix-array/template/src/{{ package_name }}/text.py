"""The text gate: lowercase letters, none to a thousand twenty-four.

A suffix is only ever as honest as the text it is read from, so the
gate keeps digits, punctuation, and uppercase out before any table is
built. The empty text passes the gate with an empty table: no suffix,
no answer, no complaint.
"""

from __future__ import annotations

MAX_LENGTH = 1024


class TextError(ValueError):
    """A candidate is no text at all."""


def ensure_text(candidate: object) -> str:
    """Return the validated text; the empty text asks for no suffix."""
    if not isinstance(candidate, str):
        raise TextError(f"not a text: {candidate!r} is not text")
    if len(candidate) > MAX_LENGTH:
        raise TextError(f"not a text: {len(candidate)} letters past {MAX_LENGTH}")
    if candidate and (not candidate.isascii() or not candidate.isalpha()):
        raise TextError(f"not a text: {candidate!r} carries a non-letter")
    if candidate != candidate.lower():
        raise TextError(f"not a text: {candidate!r} is not lowercase")
    return candidate


def ensure_pattern(candidate: object) -> str:
    """Return the validated pattern; the empty pattern asks for nothing."""
    if not isinstance(candidate, str):
        raise TextError(f"not a pattern: {candidate!r} is not text")
    if not candidate:
        raise TextError("not a pattern: the empty string")
    if len(candidate) > MAX_LENGTH:
        raise TextError(f"not a pattern: {len(candidate)} letters past {MAX_LENGTH}")
    if not candidate.isascii() or not candidate.isalpha():
        raise TextError(f"not a pattern: {candidate!r} carries a non-letter")
    if candidate != candidate.lower():
        raise TextError(f"not a pattern: {candidate!r} is not lowercase")
    return candidate


def describe(value: str) -> str:
    """The display form of a text or pattern, quoted the way the CLI prints."""
    return repr(value)
