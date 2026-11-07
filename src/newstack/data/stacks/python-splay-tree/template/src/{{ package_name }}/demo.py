"""Six stories about keys, touches, and what a tree owes its root.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import brute_sort, is_root
from .corpus import synthetic
from .tree import SplayTree


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    tree = SplayTree(corpus)

    ordered = tree.flatten() == brute_sort(corpus)
    first = Story(
        "the walk is the plain sort, exactly",
        f"{len(corpus)} keys, sort-equal={ordered}, links={tree.invariant()}",
        ordered and tree.invariant(),
    )

    probe = corpus[7]
    touched = tree.contains(probe) and is_root(tree, probe)
    second = Story(
        "a touched key rides to the root",
        f"key {probe} seated={touched}",
        touched and tree.flatten() == brute_sort(corpus),
    )

    deepest = SplayTree(list(range(1, 9)))
    deepest.contains(1)
    zig = deepest.root == 1 and deepest.flatten() == list(range(1, 9))
    third = Story(
        "a zig-zig ride lands and the walk survives",
        f"root={deepest.root}, walk-equal={deepest.flatten() == list(range(1, 9))}",
        zig,
    )

    fourth = Story(
        "min and max walk to the root on request",
        f"min={tree.minimum()}=={min(corpus)}, max={tree.maximum()}=={max(corpus)}",
        tree.root == max(corpus) and tree.minimum() == min(corpus),
    )

    survivors = [key for key in corpus[:12] if key not in corpus[3:9]]
    survivor = SplayTree(corpus[:12])
    for key in corpus[3:9]:
        survivor.remove(key)
    fifth = Story(
        "removal leaves the survivors seated",
        f"{len(survivors)} survivors of 12, "
        f"sort-equal={survivor.flatten() == brute_sort(survivors)}",
        survivor.flatten() == brute_sort(survivors) and survivor.invariant(),
    )

    edges = [
        len(SplayTree()) == 0 and SplayTree().root is None,
        SplayTree([7]).flatten() == [7] and SplayTree([7]).root == 7,
        SplayTree([1, 1, 1]).flatten() == [1] and SplayTree([1, 1, 1]).root == 1,
    ]
    sixth = Story(
        "empty, single, and duplicate keys answer quietly",
        f"edge probes held={all(edges)}",
        all(edges),
    )
    return [first, second, third, fourth, fifth, sixth]
