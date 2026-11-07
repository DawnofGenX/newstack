"""The heap itself: a forest of binomial trees, one tree per rank.

A tree of rank k holds exactly 2^k keys and no parent outranks its
children; the forest keeps one tree per rank, so the ranks standing
present are the bit pattern of the count. Meld is the product this
tool exists for: two forests union, links carry upward like binary
addition, and the smaller root of every link stays on top.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

MAX_RANK = 64


class HeapError(ValueError):
    """The forest stepped outside what a binomial shape can hold."""


def ranks_of(size: int) -> list[int]:
    """The ranks a forest of ``size`` keys must stand in: its bit pattern."""
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise HeapError(f"a forest counts whole keys, got {size!r}")
    return [rank for rank in range(size.bit_length()) if size >> rank & 1]


class Tree:
    """One binomial tree: a root-min parent and ``rank`` worth of keys."""

    __slots__ = ("children", "key", "rank", "value")

    def __init__(self, key: int, value: object = None) -> None:
        self.key = key
        self.value = value
        self.rank = 0
        self.children: list[Tree] = []

    def count(self) -> int:
        return 1 + sum(child.count() for child in self.children)

    def ordered(self) -> bool:
        """Root-min ordered, all the way down."""
        return all(
            child.ordered() and self.key <= child.key for child in self.children
        )

    def holds(self, other: Tree) -> bool:
        """Is ``other`` this tree or one of its keys, by identity."""
        return self is other or any(child.holds(other) for child in self.children)


def link(a: Tree, b: Tree) -> Tree:
    """Two equal ranks become one: the smaller root stays on top."""
    if b.key < a.key:
        a, b = b, a
    a.children.insert(0, b)
    a.rank += 1
    return a


@dataclass(frozen=True)
class Edit:
    """What one op cost: the rank the key ended in, whether it linked."""

    op: str
    rank: int
    linked: bool

    def line(self) -> str:
        return f"{self.op} rank {self.rank} linked={self.linked}"


class BinomialHeap:
    """A mergeable integer min-heap shaped as a binomial forest.

    The forest holds at most one tree per rank, a tree of rank k holds
    exactly 2^k keys, and the ranks standing present are the bit
    pattern of the count. Meld unions two forests by carrying links
    upward; pop-min lifts the smallest root and re-carries its orphans.
    """

    def __init__(self) -> None:
        self._trees: list[Tree] = []
        self._size = 0
        self._links = 0
        self._melds = 0

    # -- the forest ------------------------------------------------------

    @property
    def links(self) -> int:
        """Links spent so far: every one was a carry in an addition."""
        return self._links

    @property
    def melds(self) -> int:
        """Melds answered -- the product plain heaps refuse."""
        return self._melds

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def __iter__(self) -> Iterator[int]:
        return self.pop_all()

    def shape(self) -> list[int]:
        """The ranks standing present -- the count's bit pattern."""
        return [tree.rank for tree in self._trees]

    # -- the ops ----------------------------------------------------------

    def push(self, key: int, value: object = None) -> Edit:
        """Drop a key in; the carry answers the ranks it walked up."""
        key = _as_key(key)
        fresh = Tree(key, value)
        self._trees = self._carry([fresh, *self._trees])
        self._size += 1
        rank = -1
        linked = self._links
        for tree in self._trees:
            if tree.holds(fresh):
                rank = tree.rank
        return Edit("push", rank, self._links > linked)

    def meld(self, other: BinomialHeap) -> Edit:
        """Union two forests -- the answer plain heaps refuse to give.

        ``other`` is emptied: every key it held stands in this forest
        now, carried like any other addition.
        """
        if other is self:
            raise HeapError("a heap will not meld with itself")
        self._trees = self._carry([*self._trees, *other._trees])
        self._size += other._size
        other._trees = []
        other._size = 0
        self._melds += 1
        other._melds = 0
        return Edit("meld", max(self.shape(), default=-1), True)

    def pop(self) -> tuple[int, object]:
        """The smallest key: lift its root, re-carry the orphans."""
        if not self._trees:
            raise HeapError("the heap holds nothing")
        spot = min(range(len(self._trees)), key=lambda i: self._trees[i].key)
        root = self._trees.pop(spot)
        self._trees = self._carry(root.children + self._trees)
        self._size -= 1
        return root.key, root.value

    def pop_all(self) -> Iterator[int]:
        """Drain in sorted order -- what every shape promise buys."""
        while self._trees:
            yield self.pop()[0]

    def peek(self) -> tuple[int, object]:
        """The next pop, without paying for it."""
        if not self._trees:
            raise HeapError("the heap holds nothing")
        root = min(self._trees, key=lambda tree: tree.key)
        return root.key, root.value

    def entries(self) -> list[tuple[int, object]]:
        """Every pair held, tree by tree, root before its children."""
        held: list[tuple[int, object]] = []
        for tree in self._trees:
            _collect(tree, held)
        return held

    # -- the invariants -----------------------------------------------------

    def invariant(self) -> bool:
        """One tree per rank, rank-k trees of 2^k keys, min roots, true count."""
        seen = -1
        total = 0
        for tree in self._trees:
            if tree.rank <= seen:
                return False
            seen = tree.rank
            if tree.count() != 1 << tree.rank or not tree.ordered():
                return False
            total += 1 << tree.rank
        return total == self._size and self._size <= (1 << MAX_RANK) - 1

    def lines(self) -> list[str]:
        """The forest as a page: one line per standing rank."""
        return [
            f"tree   rank {tree.rank:2d}  keys {tree.count():4d}"
            f"  root {tree.key!r:>6}  ordered={tree.ordered()}"
            for tree in self._trees
        ]

    def stats(self) -> dict[str, object]:
        return {
            "size": self._size,
            "trees": len(self._trees),
            "ranks": self.shape(),
            "links": self._links,
            "melds": self._melds,
            "invariant": self.invariant(),
        }

    def _carry(self, trees: list[Tree]) -> list[Tree]:
        """Binary addition of forests: equal ranks link until none collide."""
        ranks: dict[int, Tree] = {}
        for tree in trees:
            while tree.rank in ranks:
                self._links += 1
                tree = link(ranks.pop(tree.rank), tree)
            ranks[tree.rank] = tree
        return [ranks[rank] for rank in sorted(ranks)]


def _collect(tree: Tree, into: list[tuple[int, object]]) -> None:
    into.append((tree.key, tree.value))
    for child in tree.children:
        _collect(child, into)


def _as_key(key: object) -> int:
    if isinstance(key, bool) or not isinstance(key, int):
        raise HeapError(f"a binomial forest orders whole numbers, got {key!r}")
    return key
