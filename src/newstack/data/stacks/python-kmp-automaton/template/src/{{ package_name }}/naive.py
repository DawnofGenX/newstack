"""The oracles: a border count and a scan with no cleverness at all.

Every answer the automaton gives must equal what this module
answers on the same strings. The border count is the longest proper
prefix that is also a suffix, found by trying lengths one by one;
the scan tries every start position and steps through letter by
letter. Overlaps are real starts, so the scan reports them all. The
automaton cannot grade its own homework from here.
"""

from __future__ import annotations


def border_length(word: str) -> int:
    """The longest proper prefix of the word that is also a suffix."""
    for size in range(len(word) - 1, -1, -1):
        if word[:size] == word[len(word) - size :]:
            return size
    return 0


def naive_starts(text: str, pattern: str) -> list[int]:
    """Every start where the pattern sits, the slow honest way.

    The empty pattern begins at every position, the way slicing `""`
    out of any offset succeeds; this is the answer the automaton
    owes, not a special case it invents.
    """
    starts: list[int] = []
    for pos in range(len(text) - len(pattern) + 1):
        if text[pos : pos + len(pattern)] == pattern:
            starts.append(pos)
    return starts


def naive_count(text: str, pattern: str) -> int:
    """How many times the pattern sits, overlaps and all."""
    return len(naive_starts(text, pattern))
