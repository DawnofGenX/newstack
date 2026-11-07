"""The Z-array: a window that never hands out a letter it has not matched.

In this array the window never hands out a letter it has not
matched: ``z[i]`` is the longest common prefix of the word and the
word from ``i`` on, cut once by the linear scan. ``z[0]`` is the
length of the word itself — the documented seat, enforced by every
audit. The window rides the word letter by letter and copies from
inside itself before it steps out, so a copy past the window edge
is a defect, not a shortcut. The derived occurrence list rides the
concatenated array and must equal the naive scan's start list, on
every word, every time.
"""

from __future__ import annotations

from .naive import naive_z
from .word import WordError, ensure_pattern, ensure_word

SEP = "\x00"


class ArrayError(ValueError):
    """The array was handed something it cannot answer."""


def _cut(word: str) -> list[int]:
    """The linear cut: copy inside the window, step out only past it."""
    size = len(word)
    values = [0] * size
    left = right = 0
    for index in range(1, size):
        if index < right:
            values[index] = min(right - index, values[index - left])
        while index + values[index] < size and word[values[index]] == word[
            index + values[index]
        ]:
            values[index] += 1
        if index + values[index] > right:
            left, right = index, index + values[index]
    if size:
        values[0] = size
    return values


def z_function(word: str) -> tuple[int, ...]:
    """The Z-array of the word: z[i] is the prefix the suffix shares.

    ``z[0]`` is ``len(word)`` — the word always matches itself
    wholly, and the empty word owns the empty array.
    """
    try:
        text = ensure_word(word)
    except WordError as refusal:
        raise ArrayError(f"no array for that: {refusal}") from refusal
    return tuple(_cut(text))


def occurrences(word: str, pattern: str) -> list[int]:
    """Every start where the pattern sits, the concatenated array's answer.

    The separator is no letter, so a run can never cross it: an
    entry at least the pattern length long is exactly a sitting.
    """
    try:
        text = ensure_word(word)
        needle = ensure_pattern(pattern)
    except WordError as refusal:
        raise ArrayError(f"no occurrences for that: {refusal}") from refusal
    if not needle:
        return list(range(len(text) + 1))
    joined = needle + SEP + text
    cut = _cut(joined)
    return [
        index - len(needle) - 1
        for index in range(len(needle) + 1, len(joined))
        if cut[index] >= len(needle)
    ]


class ZArray:
    """A word, its array, and the questions it answers."""

    def __init__(self, word: str) -> None:
        self._word = ensure_word(word)
        self._array = z_function(self._word)

    @property
    def word(self) -> str:
        return self._word

    @property
    def array(self) -> tuple[int, ...]:
        return self._array

    def starts_of(self, pattern: str) -> list[int]:
        """Every start in the word, overlaps counted as real starts."""
        return occurrences(self._word, pattern)

    def first_of(self, pattern: str) -> int | None:
        """The leftmost start, or None when the pattern never sits."""
        starts = self.starts_of(pattern)
        return starts[0] if starts else None

    def count_of(self, pattern: str) -> int:
        """How many starts the word owes, empty pattern included."""
        return len(self.starts_of(pattern))

    def audit(self) -> list[str]:
        """The array against the dumb scan; silent when clean."""
        faults: list[str] = []
        honest = naive_z(self._word)
        if self._array != honest:
            faults.append(f"array {self._array} != scan {honest}")
        if self._array and self._array[0] != len(self._word):
            faults.append(f"z[0] {self._array[0]} != {len(self._word)}")
        return faults

    def __len__(self) -> int:
        return len(self._word)
