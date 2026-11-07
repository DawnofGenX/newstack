"""The gate every text passes before the counter looks at it.

A text is a run of lowercase ASCII letters, possibly empty. No
uppercase, no digits, no spaces, no punctuation: the counter
answers runs of letters, so the letters must be the quiet kind.
The gate answers loud input with TextError and quiet input with
itself.
"""

from __future__ import annotations

MAX_TEXT = 100_000
LETTERS = "abcdefghijklmnopqrstuvwxyz"


class TextError(ValueError):
    """The string was handed over as text but is not text."""

    __slots__ = ()


def ensure_text(value: object) -> str:
    """Return the text unchanged, or refuse it naming what broke."""
    if not isinstance(value, str):
        raise TextError(f"{value!r} is not a string, so it is not text")
    if len(value) > MAX_TEXT:
        raise TextError(f"a text runs to {MAX_TEXT} letters, {value[:16]!r}... runs longer")
    for ch in value:
        if ch not in LETTERS:
            raise TextError(f"{value!r} holds {ch!r}, which is not a lowercase letter")
    return value
