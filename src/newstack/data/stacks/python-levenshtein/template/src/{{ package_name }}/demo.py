"""Six stories about letters, changes, and what a distance owes its corpus.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .distance import SHIPPED, TRIPLES, distance, rank_pairs
from .oracle import ORACLE_LIMIT, oracle_distance
from .workload import run_storm


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool

def stories() -> list[Story]:
    """The six claims the distance makes, each computed fresh."""
    pairs = [(left, right) for left in ("car", "cart", "cat", "dog")
             for right in ("do", "doc", "dog", "dogma")]
    agreed = all(distance(a, b) == oracle_distance(a, b) for a, b in pairs)
    first = Story(
        "the row walk equals the bare recursion on shipped words",
        f"{len(pairs)} shipped pairs under {ORACLE_LIMIT} letters, "
        f"oracle-equal={agreed}",
        agreed,
    )

    symmetric = all(
        distance(a, b) == distance(b, a)
        for a, b in zip(SHIPPED, SHIPPED[1:] + SHIPPED[:1], strict=True)
    )
    second = Story(
        "a distance is the same seen from either side",
        f"{len(SHIPPED)} mirrored pairs, symmetric={symmetric}",
        symmetric,
    )

    direct = [
        distance(a, c) <= distance(a, b) + distance(b, c) for a, b, c in TRIPLES
    ]
    third = Story(
        "a detour never beats the direct change",
        f"{len(TRIPLES)} shipped triples, triangle={all(direct)}",
        all(direct),
    )

    edges = [distance(word, "") for word in SHIPPED]
    fourth = Story(
        "to nothing is a change per letter",
        f"{len(edges)} words against the empty string, "
        f"exact={edges == [len(word) for word in SHIPPED]}",
        edges == [len(word) for word in SHIPPED],
    )

    corpus = list(SHIPPED)
    query = "crt"
    scan = rank_pairs(query, corpus)
    tied = [word for value, word in scan if value == scan[0][0]]
    fifth = Story(
        "nearest equals the scan's argmin, ties first by letters",
        f"{query!r} over {len(corpus)} words -> {scan[0][1]!r} at {scan[0][0]}, "
        f"head is the first of {len(tied)} tied={scan[0][1] == min(tied)}",
        scan == sorted(scan, key=lambda pair: (pair[0], pair[1]))
        and scan[0][1] == min(tied)
        and all(scan[0][0] <= value for value, _ in scan),
    )

    storm = run_storm(seed=31)
    sixth = Story(
        "a storm keeps every promise after every draw",
        f"{storm.steps} steps, {storm.breaks} breaks, {storm.checks} checks",
        storm.clean,
    )

    return [first, second, third, fourth, fifth, sixth]
