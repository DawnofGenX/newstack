"""A keyed B-tree of configurable order, keyed by integers.

Order `t` is the node's minimum degree: every node holds between `t - 1` and
`2t - 1` keys, so a full node splits down the middle and a pair of bare
siblings merges into exactly one full node. Every leaf rests at one level and
a leaf holds keys, never children, so the in-order walk — subtles, key,
subtles — is the sorted corpus whatever got the tree there.

Insertion splits a full child on the way down, which is why a node is never
overfull when a key lands in it. Deletion borrows before it merges: a short
child is refilled from a sibling across the separator, and only two short
siblings collapse, so the tree shrinks from the top and never goes jagged.
"""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

__all__ = ["BTree", "BTreeError", "NodeShape"]


class BTreeError(ValueError):
    """The tree was asked for something it cannot do."""


@dataclass(frozen=True)
class NodeShape:
    """One node as seen from outside: its depth and its key count."""

    depth: int
    keys: int
    is_leaf: bool


@dataclass
class _Node:
    keys: list[int] = field(default_factory=list)
    children: list[_Node] = field(default_factory=list)

    @property
    def leaf(self) -> bool:
        return not self.children


class BTree:
    """Keys in balance: every leaf at one level, every node inside its band."""

    def __init__(self, order: int = 3, keys: Iterable[int] = ()) -> None:
        if not isinstance(order, int) or isinstance(order, bool):
            raise BTreeError(f"order is an integer, not {type(order).__name__}")
        if order < 2:
            raise BTreeError(f"order {order} is too small: a node could not hold a key")
        self.order = order
        self._root = _Node()
        for key in keys:
            self.insert(key)

    @property
    def min_keys(self) -> int:
        """The band floor for every node below the root."""
        return self.order - 1

    @property
    def max_keys(self) -> int:
        """The band ceiling for every node, root included."""
        return 2 * self.order - 1

    @property
    def keys(self) -> list[int]:
        """The corpus, in-order: sorted, distinct, complete."""
        return list(self._walk(self._root))

    @property
    def height(self) -> int:
        """Levels that hold keys: zero for an empty tree, one for a bare leaf."""
        if self._root.leaf and not self._root.keys:
            return 0
        levels = 0
        node = self._root
        while not node.leaf:
            levels += 1
            node = node.children[0]
        return levels + 1

    @property
    def leaf_levels(self) -> int:
        """Depths that hold leaves: one, or zero for an empty tree."""
        if self._root.leaf and not self._root.keys:
            return 0
        return len(set(self._leaf_depths(self._root, 0)))

    def __len__(self) -> int:
        return len(self.keys)

    def __iter__(self) -> Iterator[int]:
        return self._walk(self._root)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, int) or isinstance(key, bool):
            return False
        return self._locate(key) is not None

    def insert(self, key: int) -> bool:
        """Insert a key. Returns False when it was already there."""
        self._need_int(key, "a tree holds integers")
        if self._locate(key) is not None:
            return False
        if len(self._root.keys) == self.max_keys:
            self._root = _Node(children=[self._root])
        self._insert_into(self._root, key)
        return True

    def delete(self, key: int) -> bool:
        """Remove a key. Returns False when it was not there."""
        self._need_int(key, "a tree holds integers")
        if self._locate(key) is None:
            return False
        self._delete_from(self._root, key)
        if not self._root.keys:
            self._root = self._root.children[0] if self._root.children else _Node()
        return True

    def lookup(self, key: int) -> bool:
        """Exact lookup: True only for a key the tree holds."""
        self._need_int(key, "a tree holds integers")
        return self._locate(key) is not None

    def range_scan(self, low: int, high: int) -> list[int]:
        """Every key in [low, high], ascending. An inverted window is refused."""
        self._need_int(low, "a window edge is an integer")
        self._need_int(high, "a window edge is an integer")
        if low > high:
            raise BTreeError(f"an empty window: {low} sits above {high}")
        return [key for key in self.keys if low <= key <= high]

    def shape(self) -> list[NodeShape]:
        """Every node, in-order, as depth and key count."""
        found: list[NodeShape] = []

        def walk(node: _Node, depth: int) -> None:
            found.append(NodeShape(depth, len(node.keys), node.leaf))
            for child in node.children:
                walk(child, depth + 1)

        walk(self._root, 0)
        return found

    def _walk(self, node: _Node) -> Iterator[int]:
        if node.leaf:
            yield from node.keys
            return
        for index, key in enumerate(node.keys):
            yield from self._walk(node.children[index])
            yield key
        yield from self._walk(node.children[-1])

    def _leaf_depths(self, node: _Node, depth: int) -> Iterator[int]:
        if node.leaf:
            yield depth
            return
        for child in node.children:
            yield from self._leaf_depths(child, depth + 1)

    def _locate(self, key: int) -> int | None:
        """Where the key sits, or None when no node answers for it."""
        node = self._root
        while True:
            index = bisect_left(node.keys, key)
            if index < len(node.keys) and node.keys[index] == key:
                return index
            if node.leaf:
                return None
            node = node.children[index]

    def _insert_into(self, node: _Node, key: int) -> None:
        index = bisect_left(node.keys, key)
        if node.leaf:
            node.keys.insert(index, key)
            return
        if len(node.children[index].keys) == self.max_keys:
            self._split_child(node, index)
            if node.keys[index] < key:
                index += 1
        self._insert_into(node.children[index], key)

    def _split_child(self, node: _Node, index: int) -> None:
        """Split a full child; the middle key rises, the halves keep the band."""
        child = node.children[index]
        middle = len(child.keys) // 2
        lifted = child.keys[middle]
        right = _Node(keys=child.keys[middle + 1 :], children=child.children[middle + 1 :])
        child.keys = child.keys[:middle]
        child.children = child.children[: middle + 1]
        node.keys.insert(index, lifted)
        node.children.insert(index + 1, right)

    def _delete_from(self, node: _Node, key: int) -> None:
        index = bisect_left(node.keys, key)
        if node.leaf:
            node.keys.pop(index)
            return
        if index < len(node.keys) and node.keys[index] == key:
            self._drop_separator(node, index, key)
            return
        self._delete_from(node.children[self._long_child(node, index)], key)

    def _drop_separator(self, node: _Node, index: int, key: int) -> None:
        """Remove a key that steers children: steal a neighbour, or merge down."""
        left, right = node.children[index], node.children[index + 1]
        if len(left.keys) > self.min_keys:
            node.keys[index] = self._pop_max(left)
            return
        if len(right.keys) > self.min_keys:
            node.keys[index] = self._pop_min(right)
            return
        left.keys.append(node.keys.pop(index))
        left.keys.extend(right.keys)
        left.children.extend(right.children)
        node.children.pop(index + 1)
        self._delete_from(left, key)

    def _long_child(self, node: _Node, index: int) -> int:
        """Make children[index] long enough to descend, and say where it went."""
        child = node.children[index]
        if len(child.keys) > self.min_keys:
            return index
        left = node.children[index - 1] if index > 0 else None
        right = (
            node.children[index + 1] if index + 1 < len(node.children) else None
        )
        if left is not None and len(left.keys) > self.min_keys:
            child.keys.insert(0, node.keys.pop(index - 1))
            node.keys.insert(index - 1, left.keys.pop())
            if not child.leaf:
                child.children.insert(0, left.children.pop())
            return index
        if right is not None and len(right.keys) > self.min_keys:
            child.keys.append(node.keys.pop(index))
            node.keys.insert(index, right.keys.pop(0))
            if not child.leaf:
                child.children.append(right.children.pop(0))
            return index
        if left is not None:
            left.keys.append(node.keys.pop(index - 1))
            left.keys.extend(child.keys)
            left.children.extend(child.children)
            node.children.pop(index)
            return index - 1
        assert right is not None  # an internal node steers at least two children
        child.keys.append(node.keys.pop(index))
        child.keys.extend(right.keys)
        child.children.extend(right.children)
        node.children.pop(index + 1)
        return index

    def _pop_max(self, node: _Node) -> int:
        """Remove and return the largest key below this node."""
        if node.leaf:
            return node.keys.pop()
        return self._pop_max(node.children[self._long_child(node, len(node.children) - 1)])

    def _pop_min(self, node: _Node) -> int:
        """Remove and return the smallest key below this node."""
        if node.leaf:
            return node.keys.pop(0)
        return self._pop_min(node.children[self._long_child(node, 0)])

    @staticmethod
    def _need_int(value: object, complaint: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise BTreeError(f"{complaint}, not {type(value).__name__}")
