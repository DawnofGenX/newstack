"""The oracles: a letter-stepper and a scan with no cleverness at all.

Every answer the Z-array gives must equal what this module answers
on the same word. The stepper walks two words side by side and
counts matching letters until one of them misses; the array scan
asks it at every position, one position at a time. The occurrence
scan tries every start in the text and steps through letter by
letter. The window cannot grade its own homework from here.
"""

from __future__ import annotations


def lcp_length(first: str, second: str) -> int:
    """How many leading letters the two words share, letters stepped."""
    limit = min(len(first), len(second))
    step = 0
    while step < limit and first[step] == second[step]:
        step += 1
    return step


def naive_z(word: str) -> tuple[int, ...]:
    """The array a dumb scan writes: the stepper at every position.

    The empty word owns the empty array, the way slicing leaves
    nothing to compare; this is the answer the window owes, not a
    special case it invents.
    """
    return tuple(lcp_length(word, word[start:]) for start in range(len(word)))


def naive_occurrences(word: str, pattern: str) -> list[int]:
    """Every start where the pattern sits in the word, the slow way.

    The empty pattern begins at every position, the way slicing ""
    out of any offset succeeds; the array must answer the same.
    """
    starts: list[int] = []
    for pos in range(len(word) - len(pattern) + 1):
        if word[pos : pos + len(pattern)] == pattern:
            starts.append(pos)
    return starts


def naive_count(word: str, pattern: str) -> int:
    """How many starts the word owes, overlaps and all."""
    return len(naive_occurrences(word, pattern))
