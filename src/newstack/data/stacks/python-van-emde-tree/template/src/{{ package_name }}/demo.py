"""Six stories about seats, clusters, and what a seek owes a scan.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import (
    brute_sort,
    scan_predecessor,
    scan_successor,
)
from .corpus import synthetic
from .keys import MAX_KEY
from .tree import VanEmdeTree


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    corpus = synthetic(64, seed=9)
    tree = VanEmdeTree(corpus)

    sought = all(
        tree.successor(query) == scan_successor(corpus, query)
        and tree.predecessor(query) == scan_predecessor(corpus, query)
        for query in range(MAX_KEY + 1)
    )
    first = Story(
        "every seek equals the scan, all universe",
        f"{len(corpus)} seats, {MAX_KEY + 1} probes, scan-equal={sought}",
        sought and tree.live() == brute_sort(corpus),
    )

    walked = tree.live() == brute_sort(corpus)
    second = Story(
        "the walk is the plain sort, exactly",
        f"{len(corpus)} seats, sort-equal={walked}",
        walked and tree.invariant(),
    )

    tree.remove(corpus[0])
    tree.remove(corpus[-1])
    survivors = brute_sort(corpus[1:-1])
    third = Story(
        "removal leaves the survivors seated",
        f"{len(survivors)} survivors of {len(corpus)}, "
        f"walk-equal={tree.live() == survivors}",
        tree.live() == survivors and tree.invariant(),
    )

    rebuilt = tree.rebuild()
    fourth = Story(
        "a rebuild from the walk answers alike",
        f"walk-equal={rebuilt.live() == tree.live()}, seated={rebuilt.invariant()}",
        rebuilt.live() == tree.live() and rebuilt.invariant(),
    )

    edges = [
        VanEmdeTree().minimum() is None,
        VanEmdeTree().successor(0) is None,
        VanEmdeTree([7]).predecessor(0) is None,
        VanEmdeTree([MAX_KEY]).successor(MAX_KEY) == MAX_KEY,
    ]
    fifth = Story(
        "empty and edge answers come back None, honestly",
        f"edge probes held={all(edges)}",
        all(edges),
    )

    whole = VanEmdeTree(range(MAX_KEY + 1))
    sixth = Story(
        "the full universe seats all two hundred fifty-six",
        f"walk-length={len(whole.live())}, audit-clean={whole.invariant()}",
        len(whole.live()) == MAX_KEY + 1 and whole.invariant(),
    )
    return [first, second, third, fourth, fifth, sixth]
