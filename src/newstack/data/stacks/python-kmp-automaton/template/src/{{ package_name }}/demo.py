"""Six stories about patterns, borders, and what a scan owes a scan.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .automaton import KmpAutomaton, scan_starts
from .corpus import synthetic
from .naive import naive_starts


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the automaton makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    text = "abracadabrabananabracadabra"

    first = KmpAutomaton("abra")
    honest = first.audit() == []
    first_story = Story(
        "the failure table is the border count, state by state",
        f"table={list(first.table)} audit-clean={honest}",
        honest,
    )

    probe = "ana"
    starts = scan_starts(text, probe)
    owed = naive_starts(text, probe)
    second = Story(
        "the starts are the naive scan's starts, exactly",
        f"pattern {probe!r} starts={starts} equal={starts == owed}",
        starts == owed,
    )

    tangle = KmpAutomaton("anana")
    overlaps = tangle.find_all("banananananas")
    third = Story(
        "overlaps are counted, not skipped",
        f"pattern {tangle.pattern!r} starts={overlaps} "
        f"count={tangle.count('banananananas')}",
        overlaps == naive_starts("banananananas", "anana") and len(overlaps) >= 2,
    )

    empty = KmpAutomaton("")
    fourth = Story(
        "the empty pattern sits at every position",
        f"len={len(text)} count={empty.count(text)}",
        empty.count(text) == len(text) + 1,
    )

    long_pattern = "abracadabra" * 4
    fifth = Story(
        "a pattern longer than the text never sits",
        f"pattern {len(long_pattern)} letters in text {len(text)} "
        f"starts={scan_starts(text, long_pattern)}",
        scan_starts(text, long_pattern) == [],
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
