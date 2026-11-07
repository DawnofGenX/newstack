"""The heap itself: a Fibonacci-ordered forest over integer keys.

The forest ranks integer-keyed items so pop-min replays the plain
`sorted(keys)` and hands every answer to the smallest root first;
decrease-key drops a tracked item and a cascading cut pays the debt
the marked-children rule books, the move ordinary heaps lack. Every figure a
node stores is re-checked from raw structure in the walk, never
trusted, and every degree stays under the documented log bound.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .keys import ensure_key


class HeapError(ValueError):
    """The heap was asked about an item it does not hold."""


@dataclass(frozen=True)
class Handle:
    """The handle push hands back; decrease-key targets by it."""

    token: int


def degree_bound(size: int) -> int:
    """The documented log ceiling on any node's degree at this size."""
    if size <= 0:
        return 0
    return math.floor(1.4405 * math.log2(size + 1)) + 2


class Node:
    """One pushed item: its key, its children, and its circle links."""

    __slots__ = ("child", "degree", "key", "left", "marked", "parent", "right", "token")

    def __init__(self, key: int, token: int) -> None:
        self.key = key
        self.token = token
        self.parent: Node | None = None
        self.child: Node | None = None
        self.degree = 0
        self.marked = False
        self.left = self
        self.right = self


def _circle_nodes(head: Node | None) -> list[Node]:
    """Every member of a sibling circle, head first, snapshot order."""
    if head is None:
        return []
    members: list[Node] = []
    cursor = head
    while True:
        members.append(cursor)
        cursor = cursor.right
        if cursor is head:
            return members


def _circle_add(head: Node | None, node: Node) -> Node:
    """Seat node in the circle behind head; return the new head."""
    if head is None:
        node.left = node
        node.right = node
        return node
    tail = head.left
    node.left = tail
    node.right = head
    tail.right = node
    head.left = node
    return head


def _circle_leave(node: Node) -> None:
    """Remove node from its circle and seat it alone."""
    node.left.right = node.right
    node.right.left = node.left
    node.left = node
    node.right = node


def _consolidate_with(head: Node | None) -> Node | None:
    """Merge equal-degree roots until degrees differ; name the min."""
    roots = _circle_nodes(head)
    if len(roots) < 2:
        return head
    table: dict[int, Node] = {}
    for root in roots:
        degree = root.degree
        while degree in table:
            other = table.pop(degree)
            if other.key < root.key:
                root, other = other, root
            _circle_leave(other)
            other.parent = root
            other.marked = False
            root.child = _circle_add(root.child, other)
            root.degree += 1
            degree += 1
        table[degree] = root
    return min(table.values(), key=lambda node: node.key)


class FibonacciHeap:
    """A forest of heap-ordered trees, roots linked, debts cascaded.

    push hands back a Handle, pop-min replays the smallest key, and
    decrease-key retunes a tracked item without a rebuild — the
    operation ordinary heaps refuse. size counts live items, peek
    names the next pop, and audit re-walks every link from structure.
    """

    def __init__(self, keys: list[int] | tuple[int, ...] | None = None) -> None:
        self._min: Node | None = None
        self._size = 0
        self._handles: dict[int, Handle] = {}
        self._next_token = 0
        for key in keys or ():
            self.push(key)

    def _mint(self, node: Node) -> Handle:
        self._next_token += 1
        handle = Handle(self._next_token)
        node.token = handle.token
        self._handles[handle.token] = handle
        return handle

    def push(self, key: int) -> Handle:
        """Seat a new item and hand back the handle decrease-key needs."""
        node = Node(ensure_key(int(key)), 0)
        handle = self._mint(node)
        self._min = _circle_add(self._min, node)
        if node.key < self._min.key:
            self._min = node
        self._size += 1
        return handle

    def pop_min(self) -> int:
        """Release the smallest key; its children inherit the seat."""
        if self._min is None:
            raise HeapError("the heap is empty")
        root = self._min
        head = root
        for child in _circle_nodes(root.child):
            child.parent = None
            head = _circle_add(head, child)
        root.child = None
        following = root.right
        _circle_leave(root)
        self._handles.pop(root.token, None)
        self._size -= 1
        self._min = _consolidate_with(None if following is root else following)
        return root.key

    def peek(self) -> int:
        """The key pop_min will release next."""
        if self._min is None:
            raise HeapError("the heap is empty")
        return self._min.key

    def __len__(self) -> int:
        return self._size

    def decrease(self, handle: Handle, key: int) -> None:
        """Drop a tracked item to a smaller key, cascading the cuts."""
        node = self._resolve(handle)
        new_key = ensure_key(int(key))
        if new_key > node.key:
            raise HeapError(f"not a decrease: {new_key} is above {node.key}")
        if new_key == node.key:
            return
        parent = node.parent
        if parent is not None and new_key < parent.key:
            self._cut(node, parent)
            self._cascading_cut(parent)
        node.key = new_key
        if self._min is None or node.key < self._min.key:
            self._min = node

    def _resolve(self, handle: Handle) -> Node:
        live = self._handles.get(handle.token)
        if live is None:
            raise HeapError(f"that handle is stale: item {handle.token} left the heap")
        for node in self._nodes():
            if node.token == handle.token:
                return node
        raise HeapError(f"that handle is stale: item {handle.token} left the heap")

    def _cut(self, node: Node, parent: Node) -> None:
        if parent.child is not None:
            siblings = _circle_nodes(parent.child)
            if len(siblings) == 1:
                parent.child = None
            else:
                parent.child = node.right
            _circle_leave(node)
        parent.degree -= 1
        node.parent = None
        node.marked = False
        self._min = _circle_add(self._min, node)

    def _cascading_cut(self, node: Node) -> None:
        parent = node.parent
        if parent is None:
            return
        if not node.marked:
            node.marked = True
            return
        self._cut(node, parent)
        self._cascading_cut(parent)



    def _nodes(self) -> list[Node]:
        """Every live node, roots first, children after their parent."""
        found: list[Node] = []

        def descend(node: Node) -> None:
            found.append(node)
            for child in _circle_nodes(node.child):
                descend(child)

        for root in _circle_nodes(self._min):
            descend(root)
        return found

    def keys(self) -> list[int]:
        """The live keys, sorted — the answer every storm is checked on."""
        return sorted(node.key for node in self._nodes())

    def degrees(self) -> list[int]:
        """Every node's stored degree, for the ceiling walk."""
        return [node.degree for node in self._nodes()]

    def audit(self) -> list[str]:
        """Every violation of rank the forest currently holds, if any."""
        faults: list[str] = []
        bound = degree_bound(max(self._size, 1))
        for node in self._nodes():
            children = _circle_nodes(node.child)
            if len(children) != node.degree:
                faults.append(f"degree {node.degree} seats {len(children)}")
            if len(children) > bound:
                faults.append(f"degree {node.degree} past bound {bound}")
            for child in children:
                if child.parent is not node:
                    faults.append(f"child {child.key} faces the wrong parent")
                if child.key < node.key:
                    faults.append(f"child {child.key} outranks {node.key}")
        if self._min is not None and any(
            root.key < self._min.key for root in _circle_nodes(self._min)
        ):
            faults.append("a root outranks the min pointer")
        return faults

    def invariant(self) -> bool:
        """True when the audit finds the forest exactly as promised."""
        return not self.audit()
