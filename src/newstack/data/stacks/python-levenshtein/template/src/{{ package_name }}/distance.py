"""Unit-cost edit distance over lowercase strings: a change costs one letter.

Insert, delete, and substitute each cost exactly one; the distance is
the fewest changes that turn one string into the other. The row walk
in ``distance`` is the answer, the bare recursion in ``oracle.py`` is
the proof, and every nearest answer must equal the brute-force scan's
argmin with ties handed to the lexicographically first entry.
"""

from __future__ import annotations

from collections.abc import Iterable

from .words import ensure_text, ensure_word

#: The shipped short words: short enough for the bare recursion to
#: stand beside them, long enough to carry letters across the matrix.
SHIPPED = (
    "car",
    "cart",
    "cat",
    "catnip",
    "dog",
    "dogma",
    "do",
    "doc",
    "knight",
    "light",
    "night",
    "book",
    "moon",
    "star",
    "start",
    "tree",
)

#: Shipped triples the triangle inequality is checked on, in the clear.
TRIPLES = (
    ("car", "cart", "cat"),
    ("dog", "dogma", "moon"),
    ("knight", "light", "night"),
    ("star", "start", "tree"),
    ("do", "doc", "dog"),
)


class DistanceError(ValueError):
    """The promise was asked of strings it cannot serve."""


def distance(left: object, right: object) -> int:
    """The fewest unit changes from ``left`` to ``right``, the standard row walk.

    The empty side is exact: a change per letter, ``distance(a, "")``
    is the length of ``a``.
    """
    a = ensure_text(left)
    b = ensure_text(right)
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        row = [i]
        for j in range(1, len(b) + 1):
            step = 0 if a[i - 1] == b[j - 1] else 1
            row.append(min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + step))
        prev = row
    return prev[len(b)]


def rank_pairs(query: object, corpus: Iterable[str]) -> list[tuple[int, str]]:
    """The brute-force scan: ``(distance, word)`` pairs, ordered by the rule.

    Entries at the same distance rank by their own letters, so the
    listing is stable however the corpus arrived.
    """
    asked = ensure_text(query)
    words = [ensure_word(word) for word in corpus]
    return sorted(((distance(asked, word), word) for word in words),
                  key=lambda pair: (pair[0], pair[1]))


def nearest(query: object, corpus: Iterable[str]) -> str:
    """The corpus entry with the smallest distance; a tie is the first word.

    The tie rule is the documented half of the promise: entries at the
    same distance rank by their own letters, and the head of the scan
    is the answer, whatever order the corpus arrived in.
    """
    ranked = rank_pairs(query, corpus)
    if not ranked:
        raise DistanceError("an empty corpus has no nearest word")
    return ranked[0][1]
