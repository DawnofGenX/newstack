"""Six stories about colours, walks, and what a tree owes its keys.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .tree import RBTree
from .workload import run_storm


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    corpus = synthetic(200, seed=9, span=220)
    tree = RBTree(corpus)
    probes = [*corpus[::17], 10**9, 0]
    answered = all(tree.has(key) is (key in set(corpus)) for key in probes)
    first = Story(
        "membership answers what a set answers",
        f"{len(probes)} probes, set-equal={answered}, size={tree.count()}",
        answered and tree.count() == len(set(corpus)),
    )

    walked = tree.keys()
    second = Story(
        "the in-order walk is the sorted list of the keys",
        f"{len(walked)} keys walked, sorted-equal={walked == sorted(set(corpus))}",
        walked == sorted(set(corpus)),
    )

    shape = tree.audit()
    third = Story(
        "the checker names nothing about the shape",
        f"audit issues={len(shape)}, black-rooted={tree.invariant()}",
        not shape and tree.invariant(),
    )

    rebuilt = RBTree(tree.keys())
    same_walk = rebuilt.keys() == tree.keys()
    fourth = Story(
        "a rebuild from the walk answers identically",
        f"walk holds {len(tree.keys())}, rebuild walks the same={same_walk}",
        same_walk and rebuilt.count() == tree.count() and rebuilt.invariant(),
    )

    storm = run_storm(seed=31)
    fifth = Story(
        "a storm keeps every promise after every op",
        f"{storm.steps} steps, {storm.breaks} breaks, seated={storm.seated}",
        storm.breaks == 0 and storm.seated,
    )

    empty = RBTree()
    lone = RBTree([7])
    removed = RBTree([4, 2, 9])
    removed.remove(9)
    sixth = Story(
        "the edges answer: empty, single-key, and removals",
        f"empty walk={empty.keys()!r}, lone walk={lone.keys()!r}, "
        f"after remove={removed.keys()!r}",
        empty.keys() == [] and empty.audit() == []
        and lone.keys() == [7] and removed.keys() == [2, 4]
        and removed.invariant(),
    )

    return [first, second, third, fourth, fifth, sixth]
