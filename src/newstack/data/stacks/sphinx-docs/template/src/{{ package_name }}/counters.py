"""`wc`-style counting, the subject this documentation site describes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Counts:
    """The three numbers ``wc`` prints, in its order."""

    lines: int
    words: int
    bytes: int


def count_text(text: str) -> Counts:
    """Count *text* the way ``wc`` does.

    >>> count_text("hello world\\n")
    Counts(lines=1, words=2, bytes=12)

    A line is a newline, so a trailing newline closes the last line instead of opening
    an empty one. Words are runs of non-whitespace. Bytes are UTF-8 bytes, which is why
    ``"héllo"`` is 6 of them and not 5.

    Raises:
        TypeError: if *text* is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"count_text expects a string, got {type(text).__name__}")
    return Counts(
        lines=text.count("\n"),
        words=len(text.split()),
        bytes=len(text.encode("utf-8")),
    )
