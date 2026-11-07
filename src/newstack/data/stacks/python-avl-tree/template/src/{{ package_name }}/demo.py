"""Six stories about keys, balance, and what a tree owes its walk.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import brute_sort, factors, height_bound
from .corpus import synthetic
from .tree import AVLTree


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    tree = AVLTree(corpus)

    ordered = tree.flatten() == brute_sort(corpus)
    first = Story(
        "the walk is the plain sort, exactly",
        f"{len(corpus)} keys, sort-equal={ordered}",
        ordered and tree.invariant(),
    )

    factors_ok = all(abs(factor) <= 1 for factor in factors(tree._root))
    second = Story(
        "every factor sits inside -1, 0, 1",
        f"{len(factors(tree._root))} nodes, smallest ceiling held={factors_ok}",
        factors_ok,
    )

    third = Story(
        "the height stays under the ceiling",
        f"height {tree.height} of {len(corpus)} keys, bound {height_bound(len(corpus))}",
        tree.height <= height_bound(len(corpus)),
    )

    rebuilt = tree.rebuild()
    fourth = Story(
        "a rebuild from the walk answers alike",
        f"walk equal={rebuilt.flatten() == tree.flatten()}, "
        f"seated={rebuilt.invariant()}",
        rebuilt.flatten() == tree.flatten() and rebuilt.invariant(),
    )

    probe = AVLTree(corpus[:12])
    for key in corpus[3:9]:
        probe.remove(key)
    survived = [key for key in corpus[:12] if key not in corpus[3:9]]
    fifth = Story(
        "removal leaves the survivors seated",
        f"{len(survived)} survivors of 12, sort-equal={probe.flatten() == survived}",
        probe.flatten() == brute_sort(survived) and probe.invariant(),
    )

    edges = [
        len(AVLTree()) == 0 and AVLTree().height == 0,
        AVLTree([7]).flatten() == [7] and AVLTree([7]).height == 1,
        AVLTree([1, 1, 1]).flatten() == [1],
    ]
    sixth = Story(
        "empty, single, and duplicate keys answer quietly",
        f"edge probes held={all(edges)}",
        all(edges),
    )
    return [first, second, third, fourth, fifth, sixth]
