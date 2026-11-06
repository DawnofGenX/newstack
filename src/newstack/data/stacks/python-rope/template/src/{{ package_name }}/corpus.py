"""Texts: where they come from, and a generator the stories trust.

A text document is whole lines kept in order, joined by newlines. Blank
lines and `#` comment lines are skipped, so a fixture can carry a note.
Both the file reader and the generator live here so the demo is
reproducible without fetching anything.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["CorpusError", "load_text", "synthetic"]


class CorpusError(ValueError):
    """A text document could not be read."""


def load_text(path: str | Path) -> str:
    """Read lines, skipping blanks and comments, joined by newlines."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such text: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a text")
    lines: list[str] = []
    for line in location.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        lines.append(entry)
    if not lines:
        raise CorpusError(f"{location} holds no text, and an empty rope proves nothing")
    return "\n".join(lines)


class _Random:
    """A small deterministic generator, so the demo text is fixed everywhere."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0xFFFF_FFFF

    def below(self, bound: int) -> int:
        self._state = (self._state * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        return self._state % bound

    def word(self) -> str:
        letters = "abcdefghijklmnopqrstuvwxyz"
        length = 3 + self.below(7)
        return "".join(letters[self.below(26)] for _ in range(length))


def synthetic(paragraphs: int, *, seed: int = 7, words: int = 8) -> str:
    """`paragraphs` lines of `words` words, fixed forever for a fixed seed."""
    if paragraphs < 1:
        raise CorpusError("a text of zero paragraphs is not a text")
    if words < 1:
        raise CorpusError("a paragraph of zero words holds no text")
    rng = _Random(seed)
    lines = [" ".join(rng.word() for _ in range(words)) for _ in range(paragraphs)]
    return "\n".join(lines)
