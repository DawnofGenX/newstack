"""Turn text into a sequence of tick events and one final summary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Counts:
    lines: int
    words: int
    bytes: int

    def as_dict(self) -> dict[str, int]:
        return {"lines": self.lines, "words": self.words, "bytes": self.bytes}


SEPARATORS = frozenset(" \t\n\r\v\f")


def count_text(text: str) -> Counts:
    raw = text.encode("utf-8")
    lines = 0
    words = 0
    inside = False
    for char in text:
        if char in SEPARATORS:
            inside = False
            if char == "\n":
                lines += 1
        elif not inside:
            inside = True
            words += 1
    return Counts(lines=lines, words=words, bytes=len(raw))


def chunks(text: str, size: int) -> list[str]:
    """Split *text* into slices of at most *size* code points, without breaking a pair."""
    if size < 1:
        raise ValueError("size must be positive")
    return [text[index : index + size] for index in range(0, len(text), size)] or [""]
