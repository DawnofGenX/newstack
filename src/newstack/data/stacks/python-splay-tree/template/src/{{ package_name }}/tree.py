"""The tree itself: a self-adjusting BST over integer keys.

a splay hands the root over, never the order. The tree seats integer
keys so the in-order walk is always the plain `sorted(keys)`, and
every access — insert, lookup, min, max — rides the touched node to
the root. The ride is three moves: zig (one rotation when the node's
parent is the root), zig-zig (rotate the grandparent first, then the
parent, when both steps lean the same way), zig-zag (rotate the
parent first, then the grandparent, when the steps lean apart). The
promise is checked, not assumed: after a hit the touched key sits at
the root, and the walk cannot tell a splay from stillness.
"""

from __future__ import annotations

from .keys import ensure_key


class TreeError(ValueError):
    """The tree was asked about a key it does not hold."""


class Node:
    """One seated key, its children, and its parent."""

    __slots__ = ("key", "left", "parent", "right")

    def __init__(self, key: int) -> None:
        self.key = key
        self.left: Node | None = None
        self.right: Node | None = None
        self.parent: Node | None = None


def _link_left(parent: Node, child: Node | None) -> None:
    """Seat a left child and tie its parent back."""
    parent.left = child
    if child is not None:
        child.parent = parent


def _link_right(parent: Node, child: Node | None) -> None:
    """Seat a right child and tie its parent back."""
    parent.right = child
    if child is not None:
        child.parent = parent


def _rotate_left(node: Node) -> Node:
    """Hand the seat to the right pivot; the walk cannot tell."""
    pivot = node.right
    assert pivot is not None
    up = node.parent
    _link_right(node, pivot.left)
    _link_left(pivot, node)
    pivot.parent = up
    if up is None:
        pass
    elif up.left is node:
        up.left = pivot
    else:
        up.right = pivot
    return pivot


def _rotate_right(node: Node) -> Node:
    """Hand the seat to the left pivot; the walk cannot tell."""
    pivot = node.left
    assert pivot is not None
    up = node.parent
    _link_left(node, pivot.right)
    _link_right(pivot, node)
    pivot.parent = up
    if up is None:
        pass
    elif up.left is node:
        up.left = pivot
    else:
        up.right = pivot
    return pivot


def _splay(root: Node, node: Node) -> Node:
    """Ride the node to the root: zig, zig-zig, or zig-zag per step.

    A zig is one rotation when the parent is the root. A zig-zig is
    two rotations, grandparent first, when parent and node lean the
    same way. A zig-zag is two rotations, parent first, when the
    steps lean apart. Every rotation is order-neutral, so the walk
    out of here is the walk that went in.
    """
    while node.parent is not None:
        parent = node.parent
        grand = parent.parent
        if grand is None:
            if node is parent.right:
                _rotate_left(parent)
            else:
                _rotate_right(parent)
        elif (node is parent.left) == (parent is grand.left):
            if parent is grand.left:
                _rotate_right(grand)
            else:
                _rotate_left(grand)
            if node is parent.left:
                _rotate_right(parent)
            else:
                _rotate_left(parent)
        else:
            if node is parent.left:
                _rotate_right(parent)
            else:
                _rotate_left(parent)
            if node is grand.left:
                _rotate_right(grand)
            else:
                _rotate_left(grand)
    node.parent = None
    return node


def _descend(root: Node | None, key: int) -> Node | None:
    """The node seating the key, or nothing. A miss touches no ride."""
    node = root
    while node is not None:
        if key == node.key:
            return node
        node = node.left if key < node.key else node.right
    return None


def _lowest(node: Node) -> Node:
    """The smallest node below this one — the end of the left road."""
    while node.left is not None:
        node = node.left
    return node


def _highest(node: Node) -> Node:
    """The largest node below this one — the end of the right road."""
    while node.right is not None:
        node = node.right
    return node


def _join(left: Node | None, right: Node | None) -> Node | None:
    """Fuse two trees where every left key is under every right key.

    The tallest of the left rides to the root and takes the right
    tree as its right child — the max walks up, min stays put.
    """
    if left is None:
        if right is not None:
            right.parent = None
        return right
    if right is None:
        left.parent = None
        return left
    top = _highest(left)
    _splay(left, top)
    _link_right(top, right)
    return top


def _check(node: Node | None, parent: Node | None, complaints: list[str]) -> int:
    """Every link re-read from raw structure; the size walked out."""
    if node is None:
        return 0
    if node.parent is not parent:
        complaints.append(f"key {node.key} answers to the wrong parent")
    size = 1
    size += _check(node.left, node, complaints)
    size += _check(node.right, node, complaints)
    return size


class SplayTree:
    """Integer keys, self-adjusting: the touch rides to the root."""

    def __init__(self, keys: object = ()) -> None:
        self._root: Node | None = None
        self._size = 0
        for key in list(keys):  # type: ignore[call-overload]
            self.insert(key)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        """Passive membership — a question, not an access, no ride."""
        if isinstance(key, bool) or not isinstance(key, int):
            return False
        return _descend(self._root, key) is not None

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.flatten())

    @property
    def root(self) -> int | None:
        """The key at the root — the last rider the tree parked."""
        return None if self._root is None else self._root.key

    def insert(self, key: object) -> None:
        """Seat a validated key and ride it to the root; twice is once.

        A duplicate is not re-seated, but it is still an access: the
        seated node rides to the root just the same.
        """
        seated = ensure_key(key)
        found = _descend(self._root, seated)
        if found is not None:
            self._root = _splay(self._root, found)
            return
        node = Node(seated)
        if self._root is None:
            self._root = node
        else:
            spot = self._root
            while True:
                if seated < spot.key:
                    if spot.left is None:
                        _link_left(spot, node)
                        break
                    spot = spot.left
                else:
                    if spot.right is None:
                        _link_right(spot, node)
                        break
                    spot = spot.right
        self._root = _splay(self._root, node)
        self._size += 1

    def contains(self, key: object) -> bool:
        """An access: a hit rides the node to the root, a miss rests."""
        if isinstance(key, bool) or not isinstance(key, int):
            return False
        found = _descend(self._root, key)
        if found is None:
            return False
        self._root = _splay(self._root, found)
        return True

    def remove(self, key: object) -> None:
        """Unseat a seated key; an absent key is refused by name."""
        if isinstance(key, bool) or not isinstance(key, int):
            raise TreeError(f"no key {key!r} to remove")
        found = _descend(self._root, key)
        if found is None:
            raise TreeError(f"no key {key} to remove")
        self._root = _splay(self._root, found)
        assert self._root is found
        left, right = self._root.left, self._root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None
        self._root = _join(left, right)
        self._size -= 1

    def minimum(self) -> int:
        """The smallest key, ridden to the root by request."""
        if self._root is None:
            raise TreeError("the tree is empty")
        self._root = _splay(self._root, _lowest(self._root))
        return self._root.key

    def maximum(self) -> int:
        """The largest key, ridden to the root by request."""
        if self._root is None:
            raise TreeError("the tree is empty")
        self._root = _splay(self._root, _highest(self._root))
        return self._root.key

    def flatten(self) -> list[int]:
        """The in-order walk — the sequence every rules table compares.

        Iterative: a splay tree may lean, and the walk should not
        care how deep the road runs.
        """
        out: list[int] = []
        stack: list[Node] = []
        node = self._root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            out.append(node.key)
            node = node.right
        return out

    def rebuild(self) -> SplayTree:
        """A fresh tree from the walk; splays preserve the sequence,
        so the rebuild must answer exactly as the original does."""
        return SplayTree(self.flatten())

    def audit(self) -> list[str]:
        """Complaints about the tree, empty when the tree is seated."""
        complaints: list[str] = []
        size = _check(self._root, None, complaints)
        if size != self._size:
            complaints.append(f"the links hold {size}, size says {self._size}")
        walked = self.flatten()
        if walked != sorted(walked):
            complaints.append("the walk is out of order")
        if len(walked) != self._size:
            complaints.append(f"the walk holds {len(walked)}, size says {self._size}")
        if self._root is not None and self._root.parent is not None:
            complaints.append("the root answers to someone")
        return complaints

    def invariant(self) -> bool:
        """The tree holds its own shape: order, links, size."""
        return not self.audit()
