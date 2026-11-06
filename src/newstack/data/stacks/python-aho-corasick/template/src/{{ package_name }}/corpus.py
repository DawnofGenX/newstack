"""Pattern lists and texts: where they come from, and generators to trust.

A pattern list is one pattern per line; blank lines and lines starting with
`#` are skipped so a fixture can carry a comment. The text corpus is kept
verbatim, the newlines included, because a match may straddle nothing but a
newline is text too. The generators are here so the demo stories reproduce
everywhere without a data file.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["CorpusError", "as_patterns", "load_patterns", "load_text", "prose"]


class CorpusError(ValueError):
    """A pattern list or a text corpus could not be read."""


def as_patterns(source: object) -> list[str]:
    """Normalize any pattern input to a list; a lone string is one pattern."""
    if isinstance(source, str):
        return [source]
    if isinstance(source, (list, tuple)):
        return list(source)
    raise CorpusError(f"patterns given as {type(source).__name__}, not a list")


def load_patterns(path: str | Path) -> list[str]:
    """Read one pattern per line, skipping blanks and comments."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such pattern list: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a pattern list")
    found: list[str] = []
    for line in location.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        found.append(entry)
    if not found:
        raise CorpusError(f"{location} holds no patterns, and nothing hunts nothing")
    return found


def load_text(path: str | Path) -> str:
    """Read a text corpus verbatim; an empty file is an empty text, legally."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such text: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a text")
    return location.read_text(encoding="utf-8")


def random_text(length: int, *, seed: int = 7, alphabet: str = "abcdefgh") -> str:
    """`length` characters drawn from `alphabet` in a fixed order per seed."""
    if length < 0:
        raise CorpusError("a text cannot be shorter than nothing")
    if not alphabet:
        raise CorpusError("an empty alphabet spells no text")
    state = seed & 0xFFFF_FFFF
    out: list[str] = []
    for _ in range(length):
        state = (state * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        out.append(alphabet[state % len(alphabet)])
    return "".join(out)


def prose(*, seed: int = 11) -> str:
    """The shipped counter corpus: deterministic words, hit-rich by design."""
    words = ("the", "hen", "she", "hers", "there", "three", "here", "horse")
    state = seed & 0xFFFF_FFFF
    out: list[str] = []
    for _ in range(160):
        state = (state * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        out.append(words[state % len(words)])
    return " ".join(out)
