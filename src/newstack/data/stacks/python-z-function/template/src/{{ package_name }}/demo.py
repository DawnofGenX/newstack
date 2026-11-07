"""Six stories about words, windows, and what an array owes a scan.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .array import ZArray, occurrences, z_function
from .corpus import synthetic
from .naive import naive_occurrences, naive_z


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the array makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    word = "abracadabrabananabracadabra"

    first = ZArray("anana")
    honest = first.audit() == []
    first_story = Story(
        "the array is the stepper's answer, entry by entry",
        f"array={list(first.array)} audit-clean={honest}",
        honest,
    )

    probe = "ana"
    starts = occurrences(word, probe)
    owed = naive_occurrences(word, probe)
    second = Story(
        "the occurrences are the naive scan's starts, exactly",
        f"pattern {probe!r} starts={starts} equal={starts == owed}",
        starts == owed,
    )

    tangle = "anana"
    overlaps = occurrences("banananananas", tangle)
    third = Story(
        "overlaps are counted, not skipped",
        f"pattern {tangle!r} starts={overlaps} count={len(overlaps)}",
        overlaps == naive_occurrences("banananananas", tangle) and len(overlaps) >= 2,
    )

    fourth = Story(
        "z[0] is the length of the word",
        f"word {first.word!r} z0={first.array[0]}",
        bool(first.array) and first.array[0] == len(first.word),
    )

    empty = ZArray("")
    fifth = Story(
        "the empty word owns the empty array",
        f"array={list(empty.array)} audit={empty.audit()}",
        empty.array == () and empty.audit() == [],
    )

    checked = all(z_function(word) == naive_z(word) for word in corpus)
    sixth = Story(
        "a seeded corpus answers like the dumb scan",
        f"{len(corpus)} words naive-equal={checked}",
        checked,
    )
    return [first_story, second, third, fourth, fifth, sixth]
