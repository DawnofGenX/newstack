"""A binary rope of cached-length chunks: a rope edits by walking, never copying.

A rope is a binary tree whose leaves hold short chunks of text and whose
internal nodes cache the length of everything below them. ``insert``,
``delete``, ``slice`` and ``append`` walk to the seam, split one leaf, and
recompute only the cached lengths along the path they touched; ``concat``
pairs two ropes without touching either; ``to_string`` is exactly
``"".join`` of the leaves in order. ``rebalance`` rebuilds the shape over
the same leaves, so balance is invisible: the text never notices.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Rope", "RopeError", "Shape"]

MAX_LEAF = 64


class RopeError(ValueError):
    """A rope operation was asked with arguments it cannot answer."""


@dataclass(frozen=True)
class Shape:
    """One node's report card: kind, text size, cached size, depth."""

    kind: str
    size: int
    depth: int


class _Leaf:
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text


class _Node:
    __slots__ = ("left", "right", "size")

    def __init__(self, left: _Tree, right: _Tree) -> None:
        self.left = left
        self.right = right
        self.size = _size(left) + _size(right)


_Tree = _Leaf | _Node


def _size(tree: _Tree) -> int:
    return tree.size if isinstance(tree, _Node) else len(tree.text)


def _height(tree: _Tree) -> int:
    if isinstance(tree, _Leaf):
        return 1
    return 1 + max(_height(tree.left), _height(tree.right))


def _texts(tree: _Tree) -> list[str]:
    if isinstance(tree, _Leaf):
        return [tree.text]
    return _texts(tree.left) + _texts(tree.right)


def _build(texts: list[str], low: int, high: int) -> _Tree:
    """A balanced tree over texts[low:high]; pairs one chunk per leaf."""
    if high - low == 1:
        return _Leaf(texts[low])
    mid = (low + high) // 2
    return _Node(_build(texts, low, mid), _build(texts, mid, high))


def _from_text(text: str, max_leaf: int) -> _Tree:
    texts = [text[i : i + max_leaf] for i in range(0, len(text), max_leaf)]
    if not texts:
        texts = [""]
    return _build(texts, 0, len(texts))


def _split_tree(tree: _Tree, at: int, seen: list[int]) -> tuple[_Tree, _Tree]:
    """Cut at a text offset; untouched subtrees are carried, not rebuilt."""
    seen[0] += 1
    if at <= 0:
        return _Leaf(""), tree
    if at >= _size(tree):
        return tree, _Leaf("")
    if isinstance(tree, _Leaf):
        return _Leaf(tree.text[:at]), _Leaf(tree.text[at:])
    left_size = _size(tree.left)
    if at == left_size:
        return tree.left, tree.right
    if at < left_size:
        head, tail = _split_tree(tree.left, at, seen)
        return head, _Node(tail, tree.right)
    head, tail = _split_tree(tree.right, at - left_size, seen)
    return _Node(tree.left, head), tail


def _budget(height_of_leaves: int) -> int:
    """The height of a balanced tree over `height_of_leaves` leaves."""
    height = 1
    span = 1
    while span < height_of_leaves:
        span *= 2
        height += 1
    return height


class Rope:
    """A text as a tree of chunks with cached lengths.

    Construction chunks the whole text once; every later edit walks the
    spine and rewrites only the cached lengths it visited. ``touches``
    carries the node count of the last operation, so the counter story —
    edit cost tracks tree depth, never text length — is measurable.
    """

    def __init__(self, text: str = "", max_leaf: int = MAX_LEAF) -> None:
        if max_leaf < 1:
            raise RopeError("a leaf of zero characters holds no text")
        if not isinstance(text, str):
            raise RopeError(f"{type(text).__name__} is not text")
        self._max_leaf = max_leaf
        self.touches = 0
        self._tree: _Tree = _from_text(text, max_leaf)

    @property
    def max_leaf(self) -> int:
        return self._max_leaf

    def __len__(self) -> int:
        return _size(self._tree)

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        """The text: literally the leaves joined, in order, nothing else."""
        return "".join(self.chunks())

    def chunks(self) -> list[str]:
        """The non-empty leaf chunks in order — the join reads these exactly."""
        return [text for text in _texts(self._tree) if text]

    def leaf_count(self) -> int:
        """Count of the non-empty chunks the spine carries."""
        return len(self.chunks())

    def height(self) -> int:
        """Longest leaf path; the budget every walk stays inside."""
        return _height(self._tree)

    def budget(self) -> int:
        """The height of a balanced tree over this many leaves."""
        return _budget(max(1, self.leaf_count()))

    def is_balanced(self) -> bool:
        """True while the tree is no deeper than a rebuild would make it."""
        return self.height() <= self.budget()

    def slice(self, start: int, stop: int | None = None) -> Rope:
        """The window as a rope; two walks, no whole-text copy."""
        size = len(self)
        lo = 0 if start < 0 else min(start, size)
        hi = size if stop is None or stop > size else max(stop, lo)
        seen = [0]
        head, _tail = _split_tree(self._tree, hi, seen)
        _before, window = _split_tree(head, lo, seen)
        rope = self._wrap(window)
        rope.touches = seen[0]
        return rope

    def insert(self, at: int, text: str) -> None:
        """Put text in at an offset; the walk is depth, not length."""
        if not isinstance(text, str):
            raise RopeError(f"{type(text).__name__} is not text")
        if not text:
            return
        size = len(self)
        pos = size + at if at < 0 else min(at, size)
        pos = max(0, pos)
        seen = [0]
        head, tail = _split_tree(self._tree, pos, seen)
        mid = _from_text(text, self._max_leaf)
        self._tree = _Node(head, _Node(mid, tail))
        self.touches = seen[0]

    def append(self, text: str) -> None:
        """Text at the very end — a concat against the whole spine."""
        self.insert(len(self), text)

    def delete(self, start: int, stop: int | None = None) -> int:
        """Remove a window; answers how many characters left the text."""
        size = len(self)
        lo = max(0, size + start if start < 0 else min(start, size))
        hi = size if stop is None else max(0, size + stop if stop < 0 else min(stop, size))
        if hi <= lo:
            return 0
        seen = [0]
        head, rest = _split_tree(self._tree, lo, seen)
        _gone, tail = _split_tree(rest, hi - lo, seen)
        self._tree = _Node(head, tail)
        self.touches = seen[0]
        return hi - lo

    def concat(self, other: Rope) -> Rope:
        """Two ropes, paired; neither one's chunks are visited or copied."""
        if not isinstance(other, Rope):
            raise RopeError(f"{type(other).__name__} is not a rope")
        joined = self._wrap(_Node(self._tree, other._tree))
        joined._max_leaf = max(self._max_leaf, other._max_leaf)
        joined.touches = 0
        return joined

    def split(self, at: int) -> tuple[Rope, Rope]:
        """Two ropes that concatenate back to exactly this text."""
        size = len(self)
        pos = max(0, size + at if at < 0 else min(at, size))
        seen = [0]
        left, right = _split_tree(self._tree, pos, seen)
        first = self._wrap(left)
        second = self._wrap(right)
        first.touches = seen[0]
        return first, second

    def rebalance(self) -> None:
        """Rebuild the shape over the same chunks: the text cannot tell."""
        before = self.to_string()
        texts = self.chunks() or [""]
        self._tree = _build(texts, 0, len(texts))
        if self.to_string() != before:  # pragma: no cover - guard rail
            raise RopeError("a rebuild never changes the text")

    def shape(self) -> list[Shape]:
        """Every node as (kind, cached size, depth), parents before leaves."""
        found: list[Shape] = []

        def walk(tree: _Tree, depth: int) -> None:
            if isinstance(tree, _Leaf):
                found.append(Shape("leaf", len(tree.text), depth))
                return
            found.append(Shape("node", tree.size, depth))
            walk(tree.left, depth + 1)
            walk(tree.right, depth + 1)

        walk(self._tree, 0)
        return found

    def _wrap(self, tree: _Tree) -> Rope:
        """A fresh rope around an existing spine — nothing is copied."""
        rope = Rope.__new__(Rope)
        rope._max_leaf = self._max_leaf
        rope.touches = 0
        rope._tree = tree
        return rope
