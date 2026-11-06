"""The tree itself: a search tree on keys, a heap on draws.

Two orders share one structure. Keys fall left and right the way a
search tree orders them; a draw decides who stands above whom, and a
parent's number never exceeds its children's. insert, delete, and the
two halves of every split are all one expression, `merge`, so the tree
is never repaired after an edit — it is re-formed, whole, from two
halves that already answered to both orders.

Same seed, same pairs, identical tree: the shape is arithmetic.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .draws import DEFAULT_SEED, Draws, expected_depth
from .keys import KeyValueError, describe, ensure_key

__all__ = ["Edit", "Treap", "TreapError"]


class TreapError(KeyValueError):
    """The tree was asked something no heap-ordered search tree answers."""


class _Node:
    __slots__ = ("key", "left", "priority", "right", "size", "value")

    def __init__(self, key: object, value: object, priority: int) -> None:
        self.key = key
        self.value = value
        self.priority = priority
        self.left: _Node | None = None
        self.right: _Node | None = None
        self.size = 1


def _size(node: _Node | None) -> int:
    return 0 if node is None else node.size


def _fix(node: _Node) -> None:
    node.size = 1 + _size(node.left) + _size(node.right)


def _merge(left: _Node | None, right: _Node | None) -> _Node | None:
    """Re-form one tree from two: every left key sorts under every right one.

    The inputs keep standing: merge copies the path it answers on and
    never relinks a node it was only shown.
    """
    if left is None:
        return right
    if right is None:
        return left
    if left.priority <= right.priority:
        node = _Node(left.key, left.value, left.priority)
        node.left = left.left
        node.right = _merge(left.right, right)
        _fix(node)
        return node
    node = _Node(right.key, right.value, right.priority)
    node.right = right.right
    node.left = _merge(left, right.left)
    _fix(node)
    return node


def _split(node: _Node | None, key: object) -> tuple[_Node | None, _Node | None]:
    """Cut at `key`: under it left, it and above it right. Nothing leaks.

    The node shown is never relinked: the cut copies its path, so the
    tree a caller handed over answers the same questions afterwards.
    """
    if node is None:
        return None, None
    if node.key < key:  # type: ignore[operator]
        under, over = _split(node.right, key)
        fresh = _Node(node.key, node.value, node.priority)
        fresh.left = node.left
        fresh.right = under
        _fix(fresh)
        return fresh, over
    under, over = _split(node.left, key)
    fresh = _Node(node.key, node.value, node.priority)
    fresh.left = over
    fresh.right = node.right
    _fix(fresh)
    return under, fresh


def _take(node: _Node | None, key: object) -> tuple[_Node | None, _Node | None]:
    """Pull the equal node out whole, or report there was none.

    Shown, never relinked: the node handed back is a copy, so the tree
    it came from keeps answering after the pull.
    """
    if node is None:
        return None, None
    if node.key == key:
        rest = _merge(node.left, node.right)
        taken = _Node(node.key, node.value, node.priority)
        return taken, rest
    if key < node.key:  # type: ignore[operator]
        found, left = _take(node.left, key)
        fresh = _Node(node.key, node.value, node.priority)
        fresh.left = left
        fresh.right = node.right
        _fix(fresh)
        return found, fresh
    found, right = _take(node.right, key)
    fresh = _Node(node.key, node.value, node.priority)
    fresh.left = node.left
    fresh.right = right
    _fix(fresh)
    return found, fresh


def _cartesian(items: list[tuple[object, object, int]]) -> _Node | None:
    """Rebuild the one tree a sorted (key, value, priority) list describes."""
    stack: list[_Node] = []
    for key, value, priority in items:
        node = _Node(key, value, priority)
        while stack and stack[-1].priority > priority:
            node.left = stack.pop()
        if stack:
            stack[-1].right = node
        stack.append(node)
    if not stack:
        return None

    def recount(node: _Node | None) -> int:
        if node is None:
            return 0
        node.size = 1 + recount(node.left) + recount(node.right)
        return node.size

    root = stack[0]
    recount(root)
    return root


def _depth(node: _Node | None) -> int:
    if node is None:
        return 0
    return 1 + max(_depth(node.left), _depth(node.right))


def _walk(node: _Node | None) -> tuple[object, ...]:
    """Preorder (key, priority) pairs: the shape as one comparable value."""
    if node is None:
        return ()
    return (node.key, node.priority, *_walk(node.left), *_walk(node.right))


def _broken(node: _Node | None, low: object, high: object) -> tuple[int, int]:
    """Count (search-order, heap-order) breaks below this node."""
    if node is None:
        return 0, 0
    bst, heap = 0, 0
    if (low is not None and node.key <= low) or (high is not None and high <= node.key):
        bst += 1
    left, right = node.left, node.right
    if left is not None and left.priority < node.priority:
        heap += 1
    if right is not None and right.priority < node.priority:
        heap += 1
    below = _broken(left, low, node.key)
    above = _broken(right, node.key, high)
    return bst + below[0] + above[0], heap + below[1] + above[1]


@dataclass(frozen=True)
class Edit:
    """What one insert or delete cost: probes, merges, and the key."""

    key: object
    changed: bool
    probes: int
    merges: int

    def line(self) -> str:
        verb = "insert" if self.changed else "repeat"
        return f"{verb:8} {describe(self.key)!r:>12} probes {self.probes} merges {self.merges}"


class Treap:
    """A binary search tree that is also a min-heap, kept so by split/merge.

    Priorities come from one seeded draw, so two trees fed the same
    pairs end up identical. `rank` answers how many stored keys sit
    strictly below, `select` asks who sits at a position, and the
    selftest checks both against `bisect` on a plain sorted list.
    """

    def __init__(self, seed: int = DEFAULT_SEED) -> None:
        self._draws = Draws(seed)
        self._root: _Node | None = None

    @classmethod
    def _hollow(cls, seed: int, root: _Node | None) -> Treap:
        tree = cls(seed)
        tree._root = root
        return tree

    @classmethod
    def from_entries(cls, entries: list[tuple[object, object, int]], seed: int) -> Treap:
        """The tree a (key, value, priority) list describes, exactly."""
        return cls._hollow(seed, _cartesian(sorted(entries, key=lambda row: row[0])))

    def __len__(self) -> int:
        return _size(self._root)

    @property
    def seed(self) -> int:
        return self._draws.seed

    def insert(self, key: object, value: object = None) -> Edit:
        """Put the pair in place; a repeat replaces the value, not the draw."""
        tagged = ensure_key(key)
        found, rest = _take(self._root, tagged)
        if found is not None:
            found.value = value
            under, over = _split(rest, tagged)
            self._root = _merge(_merge(under, found), over)
            return Edit(tagged, False, 1, 2)
        node = _Node(tagged, value, self._draws.shape_of(tagged))
        under, over = _split(rest, tagged)
        self._root = _merge(_merge(under, node), over)
        return Edit(tagged, True, 1, 2)

    def delete(self, key: object) -> Edit:
        """Take the pair out; the halves re-merge around the hole."""
        tagged = ensure_key(key)
        found, rest = _take(self._root, tagged)
        if found is None:
            return Edit(tagged, False, 1, 0)
        self._root = rest
        return Edit(tagged, True, 1, 1)

    def contains(self, key: object) -> bool:
        return self._locate(ensure_key(key)) is not None

    def get(self, key: object, default: object = None) -> object:
        """The stored value, or default when the key is not in the tree."""
        node = self._locate(ensure_key(key))
        return default if node is None else node.value

    def _locate(self, key: object) -> _Node | None:
        node = self._root
        while node is not None:
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right  # type: ignore[operator]
        return None

    def rank(self, key: object) -> int:
        """How many stored keys sit strictly below this one."""
        tagged = ensure_key(key)
        node, below = self._root, 0
        while node is not None:
            if node.key < tagged:  # type: ignore[operator]
                below += _size(node.left) + 1
                node = node.right
            elif tagged < node.key:  # type: ignore[operator]
                node = node.left
            else:
                return below + _size(node.left)
        return below

    def select(self, position: int) -> tuple[object, object]:
        """The (key, value) pair sitting at `position` in sorted order."""
        if not isinstance(position, int) or isinstance(position, bool):
            raise TreapError(f"{position!r} is not a position")
        if not 0 <= position < len(self):
            raise TreapError(f"position {position} of {len(self)} is out of range")
        node, target = self._root, position + 1
        while node is not None:
            left = _size(node.left)
            if target <= left:
                node = node.left
            elif target == left + 1:
                return node.key, node.value
            else:
                target -= left + 1
                node = node.right
        raise TreapError(f"position {position} ran off the tree")

    def predecessor(self, key: object) -> object | None:
        """The largest stored key strictly below this one, or None."""
        below = self.rank(key)
        return None if below == 0 else self.select(below - 1)[0]

    def successor(self, key: object) -> object | None:
        """The smallest stored key strictly above this one, or None."""
        above = self.rank(key) + (1 if self._locate(ensure_key(key)) is not None else 0)
        return None if above >= len(self) else self.select(above)[0]

    def items(self) -> Iterator[tuple[object, object]]:
        yield from self._inorder(self._root)

    def keys(self) -> Iterator[object]:
        for key, _ in self.items():
            yield key

    def values(self) -> Iterator[object]:
        for _, value in self.items():
            yield value

    def __iter__(self) -> Iterator[object]:
        return self.keys()

    def _inorder(self, node: _Node | None) -> Iterator[tuple[object, object]]:
        if node is None:
            return
        yield from self._inorder(node.left)
        yield node.key, node.value
        yield from self._inorder(node.right)

    def pairs(self) -> list[tuple[object, object]]:
        return list(self.items())

    def entries(self) -> list[tuple[object, object, int]]:
        """Every (key, value, priority), in sorted key order."""
        return [(node.key, node.value, node.priority) for node in self._sorted()]

    def _sorted(self) -> list[_Node]:
        out: list[_Node] = []

        def collect(node: _Node | None) -> None:
            if node is None:
                return
            collect(node.left)
            out.append(node)
            collect(node.right)

        collect(self._root)
        return out

    def window(self, low: object, high: object) -> list[tuple[object, object]]:
        """Every pair with low <= key <= high, in order, without sorting."""
        start, stop = ensure_key(low), ensure_key(high)
        if stop < start:  # type: ignore[operator]
            raise TreapError(f"{describe(high)!r} sorts before {describe(low)!r}")
        return [(key, value) for key, value in self.items() if start <= key <= stop]

    def split(self, key: object) -> tuple[Treap, Treap]:
        """Two trees at the pivot: under it left, it and above it right."""
        tagged = ensure_key(key)
        under, over = _split(self._root, tagged)
        return Treap._hollow(self.seed, under), Treap._hollow(self.seed, over)

    @staticmethod
    def join(left: Treap, right: Treap) -> Treap:
        """One tree from two: every left key must sort under every right one.

        The halves keep standing: the join clones, never relinks, so a
        caller may read its halves after the join as well as before.
        """
        left_nodes, right_nodes = left._sorted(), right._sorted()
        if left_nodes and right_nodes and not left_nodes[-1].key < right_nodes[0].key:
            raise TreapError("the halves overlap; nothing honest to merge")
        joined = [(node.key, node.value, node.priority) for node in left_nodes + right_nodes]
        return Treap._hollow(left.seed, _cartesian(joined))

    def rebuild(self) -> Treap:
        """The same (key, priority) list, rebuilt: an identical twin."""
        return Treap.from_entries(self.entries(), self.seed)

    def stats(self) -> dict[str, object]:
        """Shape facts the selftest compares against the depth promise."""
        bst, heap = _broken(self._root, None, None)
        return {
            "size": len(self),
            "depth": _depth(self._root),
            "expected_depth": expected_depth(max(len(self), 1)),
            "walk": _walk(self._root),
            "broken": (bst, heap),
            "draws": self._draws.count,
            "seed": self.seed,
        }

    def lines(self) -> list[str]:
        out = [f"size {len(self)} depth {_depth(self._root)} seed {self.seed}"]
        row: list[_Node | None] = [self._root] if self._root is not None else []
        for story in range(4):
            if not any(row):
                break
            names = [f"{describe(n.key)}:{n.priority}" if n else "." for n in row]
            out.append(f"  d{story}  " + " ".join(names))
            nxt: list[_Node | None] = []
            for node in row:
                if node is not None:
                    nxt.extend([node.left, node.right])
            row = nxt
        return out
