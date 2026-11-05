"""Counting is the product here, so it lives in one place and never guesses."""

from __future__ import annotations

from dataclasses import dataclass

SEPARATORS = frozenset({0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C})


@dataclass(frozen=True)
class Counts:
    lines: int
    words: int
    byte_count: int

    def as_dict(self) -> dict[str, int]:
        return {"lines": self.lines, "words": self.words, "bytes": self.byte_count}


def count_text(text: str) -> Counts:
    """Count lines, words and UTF-8 bytes.

    Lines are newline characters (a trailing newline ends a line but does not start
    an empty one); words are runs of non-separator characters; bytes are UTF-8 bytes,
    which is NOT the same as ``len(text)`` for anything outside ASCII.
    """
    data = text.encode("utf-8")
    lines = 0
    words = 0
    in_word = False
    for byte in data:
        if byte == 0x0A:
            lines += 1
        if byte in SEPARATORS:
            in_word = False
        elif not in_word:
            in_word = True
            words += 1
    return Counts(lines=lines, words=words, byte_count=len(data))
