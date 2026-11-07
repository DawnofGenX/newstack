"""Letter weights: how often each letter earns its place.

A frequency map is a plain dict from lowercase letters to positive
counts, ordered alphabetically so the same text always answers with
the same map. Letters the text never speaks are absent, not zero.
"""

from __future__ import annotations

from .text import LETTERS, ensure_text

Frequency = dict[str, int]


class FrequencyError(ValueError):
    """A frequency map, or the counts inside one, is malformed."""

    __slots__ = ()


def tally(text: str) -> Frequency:
    """Count the letters: alphabetical keys, positive counts, absent silences."""
    source = ensure_text(text)
    counts = {ch: source.count(ch) for ch in LETTERS}
    return {ch: n for ch, n in counts.items() if n > 0}


def ensure_frequencies(value: object) -> Frequency:
    """Return a clean alphabetical map, or refuse a malformed one."""
    if not isinstance(value, dict):
        raise FrequencyError(f"{value!r} is not a mapping, so it is no frequency map")
    items: list[tuple[str, int]] = []
    for letter, count in value.items():
        if len(letter) != 1 or letter not in LETTERS:
            raise FrequencyError(f"{letter!r} is not a lowercase letter")
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise FrequencyError(f"{letter!r} weighs {count!r}, which is no positive count")
        items.append((letter, count))
    return dict(sorted(items))
