"""The tree itself: a height-balanced BST over integer keys.

The tree seats integer keys so the in-order walk is always the plain
`sorted(keys)` and every balance factor stays inside -1, 0, 1 — a
rotation hands the height over, never loses it. Insert is idempotent,
delete of an absent key is refused by name, and every figure a node
stores is re-checked from raw structure in the selftest, not trusted.
"""

from __future__ import annotations

from .brute import height_bound
from .keys import ensure_key


class TreeError(ValueError):
    """The tree was asked about a key it does not hold."""


class Node:
    """One seated key, its children, and its stored height."""

    __slots__ = ("height", "key", "left", "right")

    def __init__(self, key: int) -> None:
        self.key = key
        self.left: Node | None = None
        self.right: Node | None = None
        self.height = 1


def _height(node: Node | None) -> int:
    """The stored height of a node, zero for nothing."""
    return 0 if node is None else node.height


def _balance(node: Node | None) -> int:
    """Left height minus right height — the factor the rules keep small."""
    if node is None:
        return 0
    return _height(node.left) - _height(node.right)


def _update(node: Node) -> None:
    """Re-seat the stored height from the children it has now."""
    node.height = 1 + max(_height(node.left), _height(node.right))


def _rotate_right(root: Node) -> Node:
    """Hand the seat to the left pivot; the walk cannot tell."""
    pivot = root.left
    assert pivot is not None
    root.left = pivot.right
    pivot.right = root
    _update(root)
    _update(pivot)
    return pivot


def _rotate_left(root: Node) -> Node:
    """Hand the seat to the right pivot; the walk cannot tell."""
    pivot = root.right
    assert pivot is not None
    root.right = pivot.left
    pivot.left = root
    _update(root)
    _update(pivot)
    return pivot


def _rebalance(root: Node) -> Node:
    """Restore the factor to -1, 0, 1 with at most one double rotation."""
    _update(root)
    factor = _balance(root)
    if factor > 1:
        assert root.left is not None
        if _balance(root.left) < 0:
            root.left = _rotate_left(root.left)
        return _rotate_right(root)
    if factor < -1:
        assert root.right is not None
        if _balance(root.right) > 0:
            root.right = _rotate_right(root.right)
        return _rotate_left(root)
    return root


def _insert(node: Node | None, key: int) -> Node:
    """Seat the key, or leave a duplicate exactly where it sits."""
    if node is None:
        return Node(key)
    if key == node.key:
        return node
    if key < node.key:
        node.left = _insert(node.left, key)
    else:
        node.right = _insert(node.right, key)
    return _rebalance(node)


def _seat_lowest(node: Node) -> tuple[int, Node | None]:
    """The smallest key in a subtree and what is left of it after."""
    if node.left is None:
        return node.key, node.right
    key, rest = _seat_lowest(node.left)
    node.left = rest
    return key, _rebalance(node)


def _remove(node: Node | None, key: int) -> Node:
    """Unseat a seated key; an absent key is refused by name."""
    if node is None:
        raise TreeError(f"no key {key} to remove")
    if key < node.key:
        node.left = _remove(node.left, key)
    elif key > node.key:
        node.right = _remove(node.right, key)
    else:
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left
        successor, rest = _seat_lowest(node.right)
        node.key, node.right = successor, rest
    return _rebalance(node)


def _walk(node: Node | None, out: list[int]) -> None:
    """In-order: left, self, right — the order the sort must match."""
    if node is None:
        return
    _walk(node.left, out)
    out.append(node.key)
    _walk(node.right, out)


def _check(node: Node | None, complaints: list[str]) -> None:
    """Every stored figure re-derived from raw structure."""
    if node is None:
        return
    _check(node.left, complaints)
    _check(node.right, complaints)
    truth = 1 + max(_height(node.left), _height(node.right))
    if node.height != truth:
        complaints.append(f"key {node.key} stores {node.height}, truth {truth}")
    if abs(_balance(node)) > 1:
        complaints.append(f"key {node.key} factor {_balance(node)} past 1")


def _depth(node: Node | None) -> int:
    """Height from raw structure, ignoring every stored figure."""
    if node is None:
        return 0
    return 1 + max(_depth(node.left), _depth(node.right))


class AVLTree:
    """Integer keys, height-balanced, walk equal to the plain sort."""

    def __init__(self, keys: object = ()) -> None:
        self._root: Node | None = None
        self._size = 0
        for key in list(keys):  # type: ignore[call-overload]
            self.insert(key)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        if isinstance(key, bool) or not isinstance(key, int):
            return False
        node = self._root
        while node is not None:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.flatten())

    @property
    def height(self) -> int:
        """Tree height from stored figures, zero for the empty tree."""
        return _height(self._root)

    def insert(self, key: object) -> None:
        """Seat a validated key; a second insert of a seated key is quiet."""
        seated = ensure_key(key)
        if seated in self:
            return
        self._root = _insert(self._root, seated)
        self._size += 1

    def remove(self, key: object) -> None:
        """Unseat a seated key; an absent key raises TreeError by name."""
        if isinstance(key, bool) or not isinstance(key, int):
            raise TreeError(f"no key {key!r} to remove")
        if key not in self:
            raise TreeError(f"no key {key} to remove")
        self._root = _remove(self._root, key)
        self._size -= 1

    def flatten(self) -> list[int]:
        """The in-order walk — the sequence every rules table compares."""
        out: list[int] = []
        _walk(self._root, out)
        return out

    def rebuild(self) -> AVLTree:
        """A fresh tree from the walk; rotations preserve the sequence,
        so the rebuild must answer exactly as the original does."""
        return AVLTree(self.flatten())

    def audit(self) -> list[str]:
        """Complaints about the tree, empty when the tree is seated."""
        complaints: list[str] = []
        _check(self._root, complaints)
        walked = self.flatten()
        if walked != sorted(walked):
            complaints.append("the walk is out of order")
        if len(walked) != self._size:
            complaints.append(f"the walk holds {len(walked)}, size says {self._size}")
        bound = height_bound(self._size)
        if _depth(self._root) > bound:
            complaints.append(f"depth {_depth(self._root)} past the bound {bound}")
        return complaints

    def invariant(self) -> bool:
        """The tree holds its own shape: order, factors, heights."""
        return not self.audit()
