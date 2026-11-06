"""The interval tree: spans keyed by start, each node carrying a max-end.

Every node remembers the highest end anywhere in its subtree — the max-end
augmentation. A stabbing or overlap query reads that one number to skip a
whole subtree it cannot answer from, and nothing else in the file lets a
query wander past a span it should have found. The promise is falsifiable
and small: for any seeded corpus the tree's answers must equal a
brute-force scan's, and the augmentation must stay true after a delete
because deletion is where remembered heights quietly rot.

A span is half-open, so the right end is never reached: a stab at an end
stands outside the span it ends.
"""

from __future__ import annotations

from .span import Interval

__all__ = ["IntervalTree", "TreeError"]


class TreeError(ValueError):
    """The tree was asked a question no set of spans can answer."""


def _key(span: Interval) -> tuple[int, int]:
    return (span.start, span.end)


class _Node:
    __slots__ = ("interval", "left", "max_end", "parent", "right")

    def __init__(self, interval: Interval) -> None:
        self.interval = interval
        self.max_end = interval.end
        self.left: _Node | None = None
        self.right: _Node | None = None
        self.parent: _Node | None = None

    @property
    def key(self) -> tuple[int, int]:
        return (self.interval.start, self.interval.end)


def _retrace(node: _Node | None) -> None:
    """Recompute max_end from here to the root; deletion calls it every time."""
    while node is not None:
        highest = node.interval.end
        if node.left is not None and node.left.max_end > highest:
            highest = node.left.max_end
        if node.right is not None and node.right.max_end > highest:
            highest = node.right.max_end
        node.max_end = highest
        node = node.parent


class IntervalTree:
    """Half-open integer spans, stabbing and overlap answers, ordered walk."""

    def __init__(self, intervals: list[Interval] | None = None) -> None:
        self._root: _Node | None = None
        self._size = 0
        for interval in intervals or []:
            self.insert(interval)

    def insert(self, interval: Interval) -> bool:
        """Add a span; a span already held lands exactly once."""
        if not isinstance(interval, Interval):
            raise TreeError(f"{interval!r} is not an Interval")
        if self._root is None:
            self._root = _Node(interval)
            self._size += 1
            return True
        node = self._root
        while True:
            if interval == node.interval:
                return False
            side = "left" if _key(interval) < node.key else "right"
            nxt = getattr(node, side)
            if nxt is None:
                fresh = _Node(interval)
                fresh.parent = node
                setattr(node, side, fresh)
                self._size += 1
                _retrace(node)
                return True
            node = nxt

    def delete(self, interval: Interval) -> bool:
        """Remove a span; the augmentation walks back up from what moved."""
        node = self._find(interval)
        if node is None:
            return False
        if node.left is not None and node.right is not None:
            successor = self._leftmost(node.right)
            node.interval = successor.interval
            node = successor
        child = node.left if node.left is not None else node.right
        parent = node.parent
        if parent is None:
            self._root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        if child is not None:
            child.parent = parent
        _retrace(parent)
        self._size -= 1
        return True

    def stab(self, point: int) -> list[Interval]:
        """Every span holding the point, ascending — equal to the scan."""
        if not isinstance(point, int) or isinstance(point, bool):
            raise TreeError(f"{point!r} is not an integer point")
        found: list[Interval] = []
        self._stab(self._root, point, found)
        return found

    def overlap(self, low: int, high: int) -> list[Interval]:
        """Every span touching [low, high), ascending — equal to the scan."""
        if not isinstance(low, int) or not isinstance(high, int):
            raise TreeError("window bounds must be integers")
        if low >= high:
            raise TreeError(f"[{low}..{high}) is an empty window to ask about")
        found: list[Interval] = []
        self._overlap(self._root, low, high, found)
        return found

    def first(self, point: int) -> Interval | None:
        """The earliest-starting span holding the point, or None."""
        found = self.stab(point)
        return found[0] if found else None

    def walk(self) -> list[Interval]:
        """Every span, ascending by (start, end) — iteration uses it."""
        found: list[Interval] = []
        self._walk(self._root, found)
        return found

    def audit(self) -> list[str]:
        """Every broken promise in the tree; empty output means healthy."""
        defects: list[str] = []
        self._audit(self._root, defects, (-10**18, -10**18), (10**18, 10**18))
        return defects

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        return iter(self.walk())

    @property
    def height(self) -> int:
        return self._height(self._root)

    def _find(self, interval: Interval) -> _Node | None:
        node = self._root
        while node is not None:
            if interval == node.interval:
                return node
            node = node.left if _key(interval) < node.key else node.right
        return None

    @staticmethod
    def _leftmost(node: _Node) -> _Node:
        while node.left is not None:
            node = node.left
        return node

    def _stab(self, node: _Node | None, point: int, found: list[Interval]) -> None:
        if node is None:
            return
        if node.left is not None and node.left.max_end > point:
            self._stab(node.left, point, found)
        if node.interval.holds(point):
            found.append(node.interval)
        if node.interval.start <= point:
            self._stab(node.right, point, found)

    def _overlap(
        self, node: _Node | None, low: int, high: int, found: list[Interval]
    ) -> None:
        if node is None:
            return
        if node.left is not None and node.left.max_end > low:
            self._overlap(node.left, low, high, found)
        if node.interval.overlaps(Interval(low, high)):
            found.append(node.interval)
        if node.interval.start < high:
            self._overlap(node.right, low, high, found)

    def _walk(self, node: _Node | None, found: list[Interval]) -> None:
        if node is None:
            return
        self._walk(node.left, found)
        found.append(node.interval)
        self._walk(node.right, found)

    def _audit(
        self,
        node: _Node | None,
        defects: list[str],
        low: tuple[int, int],
        high: tuple[int, int],
    ) -> None:
        if node is None:
            return
        if not low < node.key < high:
            defects.append(f"{node.interval.display()} sits outside its ordered band")
        expected = node.interval.end
        if node.left is not None and node.left.max_end > expected:
            expected = node.left.max_end
        if node.right is not None and node.right.max_end > expected:
            expected = node.right.max_end
        if node.max_end != expected:
            defects.append(
                f"{node.interval.display()} remembers {node.max_end}, not {expected}"
            )
        self._audit(node.left, defects, low, node.key)
        self._audit(node.right, defects, node.key, high)

    @staticmethod
    def _height(node: _Node | None) -> int:
        if node is None:
            return 0
        return 1 + max(IntervalTree._height(node.left), IntervalTree._height(node.right))
