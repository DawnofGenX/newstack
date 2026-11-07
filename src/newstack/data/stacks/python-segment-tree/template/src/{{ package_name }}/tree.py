"""A segment tree over an integer array: every node answers for its own span.

Build folds the leaf row upward, a pull-up re-folds the path a point
edit touched, and a range query walks the ladder in a bounded number of
nodes. The combine function is the seam: sum answers first, and the
same walk answers a minimum under a different fold.
"""

from __future__ import annotations

from .array import ArrayValueError, ensure_value

NEUTRAL = 0


class SegmentError(ValueError):
    """The range or index does not exist in this array."""


def addition(left: int, right: int) -> int:
    """The first fold: the window answers its total."""
    return left + right


def minimum(left: int, right: int) -> int:
    """The seam's second witness: the window answers its floor."""
    return left if left <= right else right


class SegmentTree:
    """A ladder over an integer array with point edits and range answers."""

    def __init__(self, values: object, combine: object = addition) -> None:
        rows = [ensure_value(value) for value in values]  # type: ignore[union-attr]
        self._combine = combine if callable(combine) else addition
        self._n = len(rows)
        self._size = 1 << (self._n - 1).bit_length() if self._n else 1
        self._tree: list[int | None] = [None] * (2 * self._size)
        self._tree[self._size : self._size + self._n] = rows
        for node in range(self._size - 1, 0, -1):
            self._tree[node] = self._fold(node)
        self.visits = 0

    def _fold(self, node: int) -> int | None:
        """The pull-up: a parent is its children combined."""
        left, right = self._tree[2 * node], self._tree[2 * node + 1]
        if left is None:
            return right
        if right is None:
            return left
        return self._combine(left, right)  # type: ignore[operator]

    def _merge(self, left: int | None, right: int | None) -> int | None:
        """An answer meets an answer; absence is the other's identity."""
        if left is None:
            return right
        if right is None:
            return left
        return self._combine(left, right)  # type: ignore[operator]

    def _pull(self, node: int) -> None:
        while node:
            self._tree[node] = self._fold(node)
            node >>= 1

    def query(self, low: int, high: int) -> int:
        """Answer [low, high) -- 0-based, half-open -- by walking the ladder."""
        low, high = ensure_value(low), ensure_value(high)
        if not 0 <= low <= high <= self._n:
            raise SegmentError(f"[{low}, {high}) is not inside [0, {self._n})")
        left, right = low + self._size, high + self._size
        before: int | None = None
        after: int | None = None
        visited = 0
        while left < right:
            if left & 1:
                before = self._merge(before, self._tree[left])
                left += 1
                visited += 1
            if right & 1:
                right -= 1
                after = self._merge(self._tree[right], after)
                visited += 1
            left, right = left >> 1, right >> 1
        self.visits = visited
        answer = self._merge(before, after)
        return NEUTRAL if answer is None else answer

    def set(self, index: int, value: int) -> int:
        """Drop a value onto a leaf and re-fold only its path."""
        index, value = ensure_value(index), ensure_value(value)
        self._guard(index)
        pos = self._size + index
        self._tree[pos] = value
        self._pull(pos >> 1)
        return value

    def add(self, index: int, delta: int) -> int:
        """Slide a leaf by a delta and re-fold only its path."""
        index, delta = ensure_value(index), ensure_value(delta)
        self._guard(index)
        pos = self._size + index
        self._tree[pos] = self._leaf(pos) + delta
        self._pull(pos >> 1)
        return self._tree[pos]  # type: ignore[return-value]

    def _guard(self, index: int) -> None:
        if not 0 <= index < self._n:
            raise SegmentError(f"index {index} is outside [0, {self._n})")

    def _leaf(self, pos: int) -> int:
        value = self._tree[pos]
        return NEUTRAL if value is None else value

    @property
    def n(self) -> int:
        return self._n

    @property
    def size(self) -> int:
        return self._size

    @property
    def root(self) -> int:
        answer = self._tree[1]
        return NEUTRAL if answer is None else answer

    @property
    def combine(self) -> object:
        return self._combine

    def leaves(self) -> tuple[int, ...]:
        """The leaf row: what a rebuild is allowed to start from."""
        rows = self._tree[self._size : self._size + self._n]
        return tuple(NEUTRAL if value is None else value for value in rows)

    def fingerprint(self) -> tuple[int | None, ...]:
        """The whole ladder, so a rebuild can be compared to its build."""
        return tuple(self._tree)

    def invariant(self) -> bool:
        """Every parent is still the combine of its children."""
        return all(self._tree[node] == self._fold(node) for node in range(1, self._size))

    def stats(self) -> dict[str, object]:
        return {
            "n": self._n,
            "size": self._size,
            "root": self.root,
            "visits": self.visits,
            "invariant": self.invariant(),
        }

    def lines(self) -> list[str]:
        return [
            f"array  {list(self.leaves())}",
            f"root   {self.root}",
            f"shape  size {self._size} invariant {self.invariant()}",
        ]


__all__ = [
    "NEUTRAL",
    "ArrayValueError",
    "SegmentError",
    "SegmentTree",
    "addition",
    "minimum",
]
