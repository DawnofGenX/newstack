"""A red-black tree over bounded integer keys, checked after every op.

The tree is the pair of promises: the in-order walk is the sorted list
of the keys it holds, and the checker in ``check.py`` names nothing
about the shape. Keys arrive through the gate in ``keys.py``; colours
and fixups live in ``node.py``; the tree itself is the black-rooted
shape between them.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import check, node
from .check import problems
from .keys import ensure_key


class TreeError(ValueError):
    """The tree refused an operation its keys do not support."""

    __slots__ = ()


class RBTree:
    """Integer keys in, sorted keys out, shape promised after every op."""

    def __init__(self, keys: Iterable[int] | None = None) -> None:
        self._root: node.Node | None = None
        self._size = 0
        for key in keys or ():
            self.insert(key)

    def insert(self, key: object) -> bool:
        """Store the key; False when it was already held."""
        number = ensure_key(key)
        if self.has(number):
            return False
        self._root = node.blacken(node.insert(self._root, number))
        self._size += 1
        return True

    def has(self, key: object) -> bool:
        """True only when a descent lands on the key itself."""
        number = ensure_key(key)
        walk = self._root
        while walk is not None:
            if number == walk.key:
                return True
            walk = walk.left if number < walk.key else walk.right
        return False

    def remove(self, key: object) -> None:
        """Drop the key; refuse by name when the tree never held it."""
        number = ensure_key(key)
        if not self.has(number):
            raise TreeError(f"remove of an absent key: {number}")
        self._root = node.remove(self._root, number) if self._root else None
        self._size -= 1

    def drop_min(self) -> int:
        """Drop the smallest key; refuse when the tree is empty."""
        if self._root is None:
            raise TreeError("drop_min of an empty tree")
        smallest = self._root
        while smallest.left is not None:
            smallest = smallest.left
        self._root = node.drop_min(self._root)
        self._size -= 1
        return smallest.key

    def keys(self) -> list[int]:
        """The in-order walk: the keys held, ascending."""
        found: list[int] = []
        _walk(self._root, found)
        return found

    def audit(self) -> list[str]:
        """The shape promises the checker names; empty means seated."""
        return problems(self._root)

    def invariant(self) -> bool:
        """True when the walk names nothing."""
        return check.holds(self._root)

    def count(self) -> int:
        """The keys held."""
        return self._size

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key: object) -> bool:
        return self.has(key)


def _walk(node_value: node.Node | None, found: list[int]) -> None:
    if node_value is None:
        return
    _walk(node_value.left, found)
    found.append(node_value.key)
    _walk(node_value.right, found)
