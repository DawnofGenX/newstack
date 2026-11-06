"""Key lists: where they come from, and a generator the stories trust.

A key list is one integer per line. Blank lines and lines starting with `#`
are skipped, so a fixture can carry a comment. Both the file reader and the
generator are here so the demo does not need a data file to be reproducible.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["CorpusError", "load_keys", "synthetic"]


class CorpusError(ValueError):
    """A key list could not be read."""


def load_keys(path: str | Path) -> list[int]:
    """Read one integer per line, skipping blanks and comments."""
    location = Path(path)
    if not location.exists():
        raise CorpusError(f"no such key list: {location}")
    if location.is_dir():
        raise CorpusError(f"{location} is a directory, not a key list")
    found: list[int] = []
    for line in location.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        try:
            found.append(int(entry))
        except ValueError:
            raise CorpusError(f"{location} holds {entry!r}, which is not an integer") from None
    if not found:
        raise CorpusError(f"{location} holds no keys, and a tree of nothing scans nothing")
    return found


class _Random:
    """A small deterministic generator, so the demo corpus is the same everywhere."""

    def __init__(self, seed: int) -> None:
        self._state = seed & 0xFFFF_FFFF

    def below(self, bound: int) -> int:
        self._state = (self._state * 1_664_525 + 1_013_904_223) & 0xFFFF_FFFF
        return self._state % bound


def synthetic(count: int, *, seed: int = 7, low: int = -1000, high: int = 1000) -> list[int]:
    """`count` distinct integers in [low, high), in a fixed order for a fixed seed."""
    if count < 1:
        raise CorpusError("a corpus of zero keys is not a corpus")
    if low >= high:
        raise CorpusError(f"an empty span: {low} sits at or above {high}")
    if high - low < count:
        raise CorpusError(f"{count} distinct keys cannot come from a span of {high - low}")
    rng = _Random(seed)
    keys: list[int] = []
    seen: set[int] = set()
    guard = 0
    while len(keys) < count:
        guard += 1
        if guard > count * 40:
            raise CorpusError(
                f"{count} keys cannot be drawn from this span without repeats; ask for fewer"
            )
        key = low + rng.below(high - low)
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys
