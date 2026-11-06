"""A tree that rebuilds instead of rotating, and counts what that costs.

Insertion is a plain binary search to a leaf; deletion is a plain
binary search and a splice. What separates this tree from the naive
one is the repair: no parent spins its children around; a tipped
subtree is flattened and rebuilt whole, midpoint first, same keys.

The repair walks the key's column from the root and rebuilds every
tipped ancestor it meets; a rebuild lands on midpoints, so it never
tips again and the walk terminates. Nothing is stored on a node the
walk cannot recompute: sizes, heights, and the sorted run all come
from counted traversals. `work` adds every node touch, so the counter
story — a linear charge now and then, a logarithmic average — is
arithmetic the tree itself performs.
"""

from __future__ import annotations

from .keys import ensure_key
from .rules import DEFAULT_ALPHA, checked_alpha, violates

__all__ = ["Node", "ScapegoatTree", "TreeError", "flatten", "height_of", "size_of"]


class TreeError(ValueError):
    """The tree cannot take this request."""


class Node:
    """One key, one value, two links. No sizes, no heights, no parent."""

    __slots__ = ("key", "left", "right", "value")

    def __init__(self, key: object, value: object) -> None:
        self.key = key
        self.value = value
        self.left: Node | None = None
        self.right: Node | None = None


def size_of(node: Node | None) -> int:
    """Live keys under `node`, counted by walking it."""
    if node is None:
        return 0
    return 1 + size_of(node.left) + size_of(node.right)


def height_of(node: Node | None) -> int:
    """Node count of the longest root-to-leaf chain below `node`."""
    if node is None:
        return 0
    return 1 + max(height_of(node.left), height_of(node.right))


def flatten(node: Node | None) -> list[tuple[object, object]]:
    """The subtree as a sorted run of pairs — the rebuild's raw stock."""
    if node is None:
        return []
    run = flatten(node.left)
    run.append((node.key, node.value))
    run.extend(flatten(node.right))
    return run


def _rebuild(run: list[tuple[object, object]], lo: int, hi: int) -> Node | None:
    """Midpoint first, halves after: the sorted run becomes a tree."""
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = Node(run[mid][0], run[mid][1])
    node.left = _rebuild(run, lo, mid)
    node.right = _rebuild(run, mid + 1, hi)
    return node


def breaches(node: Node | None, alpha: float) -> bool:
    """True when one child of `node` overshoots the rule right here."""
    if node is None:
        return False
    total = size_of(node)
    return violates(alpha, size_of(node.left), total) or violates(
        alpha, size_of(node.right), total
    )


class ScapegoatTree:
    """Ordered pairs; repairs are rebuilds; every touch is counted."""

    def __init__(self, alpha: float = DEFAULT_ALPHA) -> None:
        self.alpha = checked_alpha(alpha)
        self.root: Node | None = None
        self.work = 0

    def __len__(self) -> int:
        return size_of(self.root)

    def _touch(self, steps: int = 1) -> None:
        self.work += steps

    def insert(self, key: object, value: object) -> bool:
        """Search to a leaf, then rebuild the tipped ancestors.

        Returns True when a key arrived, False when an old key was
        re-valued in place.
        """
        key = ensure_key(key)
        self._touch()
        node = self.root
        if node is None:
            self.root = Node(key, value)
            return True
        while True:
            self._touch()
            if key == node.key:
                node.value = value
                return False
            if key < node.key:
                if node.left is None:
                    node.left = Node(key, value)
                    break
                node = node.left
            else:
                if node.right is None:
                    node.right = Node(key, value)
                    break
                node = node.right
        self._repair(key)
        return True

    def delete(self, key: object) -> bool:
        """Splice the key out, then rebuild the tipped ancestors."""
        key = ensure_key(key)
        self._touch()
        node = self.root
        parent: Node | None = None
        while node is not None and node.key != key:
            self._touch()
            parent = node
            node = node.left if key < node.key else node.right
        if node is None:
            return False
        if node.left is not None and node.right is not None:
            heir_parent = node
            heir = node.right
            while heir.left is not None:
                self._touch()
                heir_parent = heir
                heir = heir.left
            node.key, node.value, heir.key, heir.value = (
                heir.key,
                heir.value,
                node.key,
                node.value,
            )
            if heir_parent is node:
                node.right = heir.right
            else:
                heir_parent.left = heir.right
        else:
            replacement = node.left if node.left is not None else node.right
            if node is self.root:
                self.root = replacement
            elif parent is not None and parent.left is node:
                parent.left = replacement
            elif parent is not None:
                parent.right = replacement
        self._repair(key)
        return True

    def _repair(self, key: object) -> None:
        """Rebuild every tipped ancestor along the key's column.

        The walk charges one touch per ancestor read; each flattening
        and rebuilding charges its size twice over. A rebuild lands on
        midpoints and never tips again, so the column is rebuilt at
        most one tipped ancestor deep per level, and the walk stops
        with the column.
        """
        parent: Node | None = None
        node = self.root
        while node is not None:
            self._touch()
            if breaches(node, self.alpha):
                run = flatten(node)
                self._touch(len(run) * 2)
                fresh = _rebuild(run, 0, len(run))
                if parent is None:
                    self.root = fresh
                elif node is parent.left:
                    parent.left = fresh
                else:
                    parent.right = fresh
                node = fresh
            if key == node.key:
                return
            parent = node
            node = node.left if key < node.key else node.right

    def get(self, key: object, default: object = None) -> object:
        key = ensure_key(key)
        node = self.root
        while node is not None:
            self._touch()
            if key == node.key:
                return node.value
            node = node.left if key < node.key else node.right
        return default

    def __contains__(self, key: object) -> bool:
        sentinel = object()
        return self.get(key, sentinel) is not sentinel

    def rank(self, key: object) -> int:
        """Stored keys strictly below `key` — counted, never stored."""
        key = ensure_key(key)
        below = 0
        node = self.root
        while node is not None:
            self._touch()
            if key <= node.key:
                node = node.left
            else:
                below += size_of(node.left) + 1
                node = node.right
        return below

    def select(self, position: int) -> tuple[object, object]:
        """The pair at `position` in sorted order; error past the end."""
        if isinstance(position, bool) or not isinstance(position, int):
            raise TreeError(f"{position!r} is not a position")
        total = len(self)
        if not 0 <= position < total:
            raise TreeError(f"position {position} is outside a tree of {total}")
        node = self.root
        while node is not None:
            self._touch()
            left = size_of(node.left)
            if position == left:
                return node.key, node.value
            if position < left:
                node = node.left
            else:
                position -= left + 1
                node = node.right
        raise TreeError("the walk left the tree mid-position")

    def keys(self):
        yield from (pair[0] for pair in flatten(self.root))

    def pairs(self) -> list[tuple[object, object]]:
        return flatten(self.root)

    def depth(self) -> int:
        return height_of(self.root)

    def balanced(self) -> bool:
        """Every node here keeps both children inside the rule."""
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node is None:
                continue
            if breaches(node, self.alpha):
                return False
            stack.append(node.left)
            stack.append(node.right)
        return True

    def stats(self) -> dict[str, int]:
        return {
            "size": len(self),
            "depth": self.depth(),
            "work": self.work,
            "balanced": int(self.balanced()),
        }
