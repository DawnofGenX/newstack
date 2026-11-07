"""The oracles: a scan with no hash and no cleverness at all.

Every answer the rolling scanner gives must equal what this module
answers on the same strings. The scan tries every start position
and steps through letter by letter — no base, no modulus, no
shortcut. Overlaps are real starts, so the scan reports them all.
The scanner cannot grade its own homework from here.
"""

from __future__ import annotations


def naive_starts(text: str, pattern: str) -> list[int]:
    """Every start where the pattern sits, the slow honest way.

    The empty pattern begins at every position, the way slicing `""`
    out of any offset succeeds; this is the answer the scanner owes,
    not a special case it invents.
    """
    starts: list[int] = []
    for pos in range(len(text) - len(pattern) + 1):
        if text[pos : pos + len(pattern)] == pattern:
            starts.append(pos)
    return starts


def naive_count(text: str, pattern: str) -> int:
    """How many times the pattern sits, overlaps and all."""
    return len(naive_starts(text, pattern))
