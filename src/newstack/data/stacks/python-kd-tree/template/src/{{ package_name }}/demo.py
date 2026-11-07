"""Six stories about splits, boxes, and what a tree owes its corpus.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .scan import scan_has, scan_nearest, scan_range
from .tree import KDTree
from .workload import run_storm


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    corpus = synthetic(200, seed=9, span=80)
    tree = KDTree(corpus)

    probes = [*corpus[::17], (10**9, -10**9), (0, 0)]
    answered = all(
        tree.has(point) is scan_has(corpus, point) for point in probes
    )
    first = Story(
        "membership answers what a set answers",
        f"{len(probes)} probes, set-equal={answered}, size={tree.count()}",
        answered and tree.count() == len(set(corpus)),
    )

    boxes = [(0, 0, 10, 10), (-80, -80, 80, 80), (5, 5, 5, 5), (100, 100, 200, 200)]
    listed = all(tree.range(box) == scan_range(corpus, box) for box in boxes)
    second = Story(
        "every rectangle answer equals the brute-force filter",
        f"{len(boxes)} boxes checked, scan-equal={listed}",
        listed,
    )

    queries = [(0, 0), (-1, -1), corpus[7], corpus[11], (79, -79)]
    matched = all(
        tree.nearest(query) == scan_nearest(corpus, query) for query in queries
    )
    third = Story(
        "the nearest answer equals the brute-force argmin",
        f"{len(queries)} queries, argmin-equal={matched}, tie=smallest point",
        matched,
    )

    rebuilt = KDTree(tree.walk())
    same_walk = sorted(rebuilt.walk()) == sorted(tree.walk())
    fourth = Story(
        "a rebuild from the in-order walk answers identically",
        f"walk holds {len(tree.walk())}, rebuild walks the same={same_walk}",
        same_walk and rebuilt.count() == tree.count(),
    )

    storm = run_storm(seed=31)
    fifth = Story(
        "a storm keeps every promise after every op",
        f"{storm.steps} steps, {storm.breaks} breaks, seated={storm.seated}",
        storm.breaks == 0 and storm.seated,
    )

    empty = KDTree()
    lone = KDTree([(3, 4)])
    sixth = Story(
        "the edges answer: empty and single-point trees",
        f"empty nearest={empty.nearest((0, 0))!r}, lone nearest="
        f"{lone.nearest((0, 0))!r}, lone holds={(3, 4) in lone.walk()}",
        empty.nearest((0, 0)) is None
        and empty.walk() == []
        and lone.nearest((0, 0)) == (3, 4)
        and lone.walk() == [(3, 4)],
    )

    return [first, second, third, fourth, fifth, sixth]
