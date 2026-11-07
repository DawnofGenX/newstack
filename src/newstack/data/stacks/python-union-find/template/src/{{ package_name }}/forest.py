"""A disjoint-set forest over integer elements: union by size, path compression.

Every element carries one parent pointer and the forest answers for
everyone below it with one name: two elements share a component exactly
when their walks land on the same root. Links point at roots and the
size rides on the root, so a merge rewrites nothing and depth stays
logarithmic before compression is ever asked for. Deletions are out of
scope on purpose: a component that loses a member is a different
question, and this forest does not answer it.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

__all__ = ["Shape", "UnionFind", "UnionFindError"]

MAX_RANK_BITS = 64


class UnionFindError(ValueError):
    """The elements or pairs do not describe a forest."""


def _ensure_element(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise UnionFindError(f"{value!r} is not an integer element")
    return value


@dataclass(frozen=True)
class Shape:
    """What the forest looks like from the outside, at one instant."""

    elements: int
    components: int
    max_depth: int
    roots_rewritten: int


class UnionFind:
    """A disjoint-set forest over integer elements.

    ``find`` walks to the root and compresses the path on the way back;
    ``union`` links the smaller root under the larger one. Both promises
    are arithmetic, and the selftest re-checks them after real histories.
    """

    def __init__(self, elements: Iterable[int] = ()) -> None:
        self._parent: dict[int, int] = {}
        self._size: dict[int, int] = {}
        self._rewritten = 0
        for value in elements:
            self.add(value)

    def add(self, element: int) -> bool:
        """Open a component of one. False if the element is already in."""
        value = _ensure_element(element)
        if value in self._parent:
            return False
        self._parent[value] = value
        self._size[value] = 1
        return True

    def __contains__(self, element: object) -> bool:
        return isinstance(element, int) and element in self._parent

    def __len__(self) -> int:
        return len(self._parent)

    def __iter__(self) -> Iterator[int]:
        return iter(sorted(self._parent))

    @property
    def count(self) -> int:
        """How many components the forest holds right now."""
        return sum(1 for element in self._parent if self._root(element) == element)

    def root_of(self, element: int) -> int:
        """Which element names this one's component. No compression here."""
        value = self._check(element)
        return self._root(self._parent[value])

    def find(self, element: int) -> int:
        """Which element names this one's component, compressing on return.

        The walk is deliberately plain before the return: compression
        rewrites parents toward the root, so the answer cannot change.
        """
        value = self._check(element)
        root = self._root(self._parent[value])
        node = self._parent[value]
        while node != root:
            ahead = self._parent[node]
            self._parent[node] = root
            self._rewritten += 1
            node = ahead
        return root

    def union(self, first: int, second: int) -> bool:
        """Merge two components. False if they already share a name."""
        left = self.find(first)
        right = self.find(second)
        if left == right:
            return False
        if self._size[left] < self._size[right]:
            left, right = right, left
        self._parent[right] = left
        self._size[left] += self._size[right]
        del self._size[right]
        return True

    def connected(self, first: int, second: int) -> bool:
        """Whether two walks end on the same name."""
        return self.find(first) == self.find(second)

    def components(self) -> list[list[int]]:
        """Every component, members ascending, groups by smallest member."""
        groups: dict[int, list[int]] = {}
        for element in sorted(self._parent):
            groups.setdefault(self._root(self._parent[element]), []).append(element)
        # members arrive ascending, so the first member names the group
        return [groups[member] for member in sorted(groups, key=lambda root: groups[root][0])]

    def snapshot(self) -> list[tuple[int, int]]:
        """(element, root) pairs in ascending element order, no compression."""
        return [(element, self._root(self._parent[element])) for element in self._parent]

    @classmethod
    def from_snapshot(cls, pairs: Mapping[int, int] | Iterable[tuple[int, int]]) -> UnionFind:
        """Rebuild a forest from (element, root) pairs. Renders no history."""
        items = pairs.items() if isinstance(pairs, Mapping) else pairs
        forest = cls()
        roots: dict[int, int] = {}
        for element, root in items:
            value = _ensure_element(element)
            named = _ensure_element(root)
            if value in roots and roots[value] != named:
                raise UnionFindError(
                    f"{value} answers to {roots[value]} and to {named}; one name only"
                )
            roots[value] = named
            forest.add(value)
        for value, named in roots.items():
            if named not in forest._parent:
                raise UnionFindError(f"{value} answers to {named}, which is not an element")
        for value, named in roots.items():
            if named != value:
                forest._parent[value] = named
        forest._size = {}
        for value in roots.values():
            forest._size[value] = forest._size.get(value, 0) + 1
        return forest

    def shape(self) -> Shape:
        """Element count, component count, depth, and what compression rewrote."""
        return Shape(
            elements=len(self._parent),
            components=self.count,
            max_depth=max(
                (self._depth(element) for element in self._parent),
                default=0,
            ),
            roots_rewritten=self._rewritten,
        )

    def _check(self, element: int) -> int:
        value = _ensure_element(element)
        if value not in self._parent:
            raise UnionFindError(f"{value} is not in the forest")
        return value

    def _root(self, value: int) -> int:
        node = value
        while self._parent[node] != node:
            node = self._parent[node]
        return node

    def _depth(self, element: int) -> int:
        depth = 0
        node = element
        while self._parent[node] != node:
            node = self._parent[node]
            depth += 1
        return depth
