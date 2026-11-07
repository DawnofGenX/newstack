"""Rabin-Karp: the rolling window, the checked candidate, the starts.

The scanner weighs every width-wide window with the documented
rolling hash and, whenever a window's digest equals the pattern's,
it *still* walks the letters: a digest is a question, the
letter-by-letter comparison is the answer, and the rolling window
never forgets a letter it is standing on. Collisions are honest
— they cost a comparison, never a wrong start. The scan's
start list must equal the naive scan's, exactly, on every shipped
corpus; overlaps are counted, not skipped, so `ana` inside `banana`
starts twice.
"""

from __future__ import annotations

from .hashing import (
    HashError,
    leading_power,
    roll,
    window_hash,
)
from .pattern import PatternError, ensure_pattern, ensure_text


class ScannerError(ValueError):
    """The scanner was handed something it cannot answer."""


def _letters_agree(window: str, pattern: str) -> bool:
    """The candidate check: letter by letter, no slicing shortcuts."""
    if len(window) != len(pattern):
        return False
    return all(left == right for left, right in zip(window, pattern, strict=True))


def scan_starts(text: str, pattern: str) -> list[int]:
    """Every start where the pattern sits in the text, overlaps kept."""
    try:
        hay = ensure_text(text)
        needle = ensure_pattern(pattern)
    except PatternError as refusal:
        raise ScannerError(f"no scan for that: {refusal}") from refusal
    width = len(needle)
    if width == 0:
        return list(range(len(hay) + 1))
    if width > len(hay):
        return []
    wanted = window_hash(needle)
    digest = window_hash(hay[:width])
    starts: list[int] = []
    if digest == wanted and _letters_agree(hay[:width], needle):
        starts.append(0)
    for start in range(1, len(hay) - width + 1):
        digest = roll(digest, hay[start - 1], hay[start + width - 1], width)
        if digest == wanted and _letters_agree(hay[start : start + width], needle):
            starts.append(start)
    return starts


class RollingScanner:
    """A pattern, its digest, and the questions the rolling scan answers."""

    def __init__(self, pattern: str) -> None:
        try:
            self._pattern = ensure_pattern(pattern)
        except PatternError as refusal:
            raise ScannerError(f"no scanner for that: {refusal}") from refusal
        self._digest = window_hash(self._pattern)
        self._weight = leading_power(len(self._pattern))

    @property
    def pattern(self) -> str:
        return self._pattern

    @property
    def digest(self) -> int:
        return self._digest

    def find_all(self, text: str) -> list[int]:
        """Every start in order, overlaps counted as real starts."""
        return scan_starts(text, self._pattern)

    def find_first(self, text: str) -> int | None:
        """The leftmost start, or None when the pattern never sits."""
        starts = self.find_all(text)
        return starts[0] if starts else None

    def count(self, text: str) -> int:
        """How many starts the text owes, empty pattern included."""
        return len(self.find_all(text))

    def collisions(self, text: str) -> int:
        """Digest matches the letters refused: the tax the modulus charges.

        An honest scanner still checks every candidate, so a
        collision costs a comparison and never a wrong start. This
        counts the tax, not a defect.
        """
        width = len(self._pattern)
        hay = ensure_text(text)
        if width == 0 or width > len(hay):
            return 0
        seen = set(self.find_all(hay))
        tax = 0
        digest = window_hash(hay[:width])
        if digest == self._digest and 0 not in seen:
            tax += 1
        for start in range(1, len(hay) - width + 1):
            digest = roll(digest, hay[start - 1], hay[start + width - 1], width)
            if digest == self._digest and start not in seen:
                tax += 1
        return tax

    def audit(self, text: str) -> list[str]:
        """Every rolled digest against a fresh weigh; silent when clean.

        The law the scanner lives under: after any number of rolls
        the digest equals ``window_hash`` of the window it stands
        on. A break here means the scan is fiction.
        """
        faults: list[str] = []
        width = len(self._pattern)
        hay = ensure_text(text)
        if width == 0 or width > len(hay):
            return faults
        digest = window_hash(hay[:width])
        if digest != window_hash(hay[:width]):
            faults.append(f"window 0: rolled {digest} != fresh")
        for start in range(1, len(hay) - width + 1):
            digest = roll(digest, hay[start - 1], hay[start + width - 1], width)
            honest = window_hash(hay[start : start + width])
            if digest != honest:
                faults.append(f"window {start}: rolled {digest} != fresh {honest}")
        return faults

    def __len__(self) -> int:
        return len(self._pattern)


__all__ = [
    "HashError",
    "RollingScanner",
    "ScannerError",
    "scan_starts",
]
