"""Turning a document into the set that similarity is defined on.

The choice of shingle is the whole definition of "similar": a word-level
5-shingle and a character-level 5-shingle answer different questions, and a
document that only differs in whitespace produces the same set.
"""

from __future__ import annotations

import re

WORD = re.compile(r"[a-z0-9]+")


class ShingleError(ValueError):
    """A shingle size or a document that cannot produce shingles."""


def normalize(text: str) -> str:
    """Lowercase, and collapse every run of non-word characters into one space."""
    return " ".join(WORD.findall(text.lower()))


def shingles(text: str, size: int = 5) -> frozenset[str]:
    """The set of word `size`-shingles of a document."""
    if size < 1:
        raise ShingleError(f"a shingle needs at least one word, not {size}")
    words = normalize(text).split()
    if not words:
        raise ShingleError("a document with no words has no shingles")
    if len(words) < size:
        # A short document is its own single shingle: dropping it would make two
        # identical short documents look unrelated.
        return frozenset([" ".join(words)])
    return frozenset(
        " ".join(words[start : start + size]) for start in range(len(words) - size + 1)
    )


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    """The exact Jaccard similarity: what every estimate in this project is judged against."""
    if not left and not right:
        raise ShingleError("two empty sets have no similarity to report")
    union = left | right
    return len(left & right) / len(union)
