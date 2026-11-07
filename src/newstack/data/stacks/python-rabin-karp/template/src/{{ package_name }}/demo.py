"""Six stories about windows, digests, and what a scan owes a scan.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .hashing import roll, window_hash
from .naive import naive_starts
from .scanner import RollingScanner, scan_starts


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the scanner makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    text = "abracadabrabananabracadabra"

    first = RollingScanner("abra")
    clean = first.audit(text) == []
    first_story = Story(
        "the roll equals the fresh weigh, window after window",
        f"digest={first.digest} audit-clean={clean}",
        clean,
    )

    probe = "ana"
    starts = scan_starts(text, probe)
    owed = naive_starts(text, probe)
    second = Story(
        "the starts are the naive scan's starts, exactly",
        f"pattern {probe!r} starts={starts} equal={starts == owed}",
        starts == owed,
    )

    tangle = RollingScanner("anana")
    overlaps = tangle.find_all("banananananas")
    third = Story(
        "overlaps are counted, not skipped",
        f"pattern {tangle.pattern!r} starts={overlaps} "
        f"count={tangle.count('banananananas')}",
        overlaps == naive_starts("banananananas", "anana") and len(overlaps) >= 2,
    )

    window = "abraca"
    rolled = roll(window_hash(window[:5]), window[0], window[5], 5)
    honest = window_hash(window[1:])
    fourth = Story(
        "one roll spares the letters, never the truth",
        f"rolled={rolled} fresh={honest} equal={rolled == honest}",
        rolled == honest,
    )

    empty = RollingScanner("")
    fifth = Story(
        "the empty pattern sits at every position",
        f"len={len(text)} count={empty.count(text)}",
        empty.count(text) == len(text) + 1,
    )

    checked = all(
        scan_starts(text, pattern) == naive_starts(text, pattern)
        for pattern in corpus
    )
    sixth = Story(
        "a seeded corpus answers like the naive scan",
        f"{len(corpus)} patterns naive-equal={checked}",
        checked,
    )
    return [first_story, second, third, fourth, fifth, sixth]
