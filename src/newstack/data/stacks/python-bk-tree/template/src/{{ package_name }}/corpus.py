"""Words: where they come from, and a deterministic generator for the stories.

A corpus is one word per line. Blank lines and lines starting with `#` are
skipped, so a fixture can carry a comment. Both the file reader and the
generator are here so the demo does not need a data file to be reproducible.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["CorpusError", "dedupe", "load_words", "synthetic"]


class CorpusError(ValueError):
    """A word list could not be read."""


def load_words(path: str | Path, *, lowercase: bool = False) -> list[str]:
    """Read one word per line, skipping blanks and comments."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such word list: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a word list")
    found: list[str] = []
    text = location.read_text(encoding="utf-8")
    for line in text.splitlines():
        word = line.strip()
        if not word or word.startswith("#"):
            continue
        if lowercase:
            word = word.lower()
        found.append(word)
    if not found:
        raise CorpusError(f"{location} holds no words, and a tree of nothing finds nothing")
    return found


def dedupe(words: list[str]) -> list[str]:
    """Keep the first of each word, in the order they arrived."""
    seen: set[str] = set()
    kept: list[str] = []
    for word in words:
        if word in seen:
            continue
        seen.add(word)
        kept.append(word)
    return kept


class _Random:
    """A small deterministic generator, so the demo corpus is the same everywhere."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0xFFFF_FFFF

    def below(self, bound: int) -> int:
        self._state = (self._state * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        return self._state % bound


_ONSETS = ("b", "c", "d", "f", "g", "h", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w")
_VOWELS = ("a", "e", "i", "o", "u")
_CODAS = ("", "n", "r", "t", "s", "l", "ck")


def synthetic(count: int, *, seed: int = 7, syllables: tuple[int, ...] = (2, 3, 4)) -> list[str]:
    """`count` distinct pronounceable words, in a fixed order for a fixed seed."""
    if count < 1:
        raise CorpusError("a corpus of zero words is not a corpus")
    rng = _Random(seed)
    words: list[str] = []
    seen: set[str] = set()
    guard = 0
    while len(words) < count:
        guard += 1
        if guard > count * 40:
            raise CorpusError(
                f"{count} words cannot be built from these syllables without repeats; ask for fewer"
            )
        parts = syllables[rng.below(len(syllables))]
        letters: list[str] = []
        for _ in range(parts):
            letters.append(_ONSETS[rng.below(len(_ONSETS))])
            letters.append(_VOWELS[rng.below(len(_VOWELS))])
        letters.append(_CODAS[rng.below(len(_CODAS))])
        word = "".join(letters)
        if word in seen:
            continue
        seen.add(word)
        words.append(word)
    return words
