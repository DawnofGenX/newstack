"""The answers computed with no structure at all: the oracle side.

A heap earns trust the way every order does — by matching a dumber
method. The sort here touches no links, and the exposure walk reads
raw structure without asking the heap a single question, so a stale
degree or a flipped parent shows up as a disagreement, not a silence.
"""

from __future__ import annotations

from .heap import FibonacciHeap, Node


def naive_sort(keys: list[int]) -> list[int]:
    """The answer every pop sequence must replay: plain sorted()."""
    return sorted(keys)


def naive_min(keys: list[int]) -> int:
    """The next release of a non-empty pile, no heap involved."""
    if not keys:
        raise ValueError("the pile is empty")
    return min(keys)


def _circle_snapshot(head: Node | None) -> list[Node]:
    """Members of a sibling circle read from raw links only."""
    if head is None:
        return []
    members: list[Node] = []
    cursor = head
    while True:
        members.append(cursor)
        cursor = cursor.right
        if cursor is head:
            return members


def _descend(node: Node, found: list[Node]) -> None:
    found.append(node)
    for child in _circle_snapshot(node.child):
        _descend(child, found)


def expose(heap: FibonacciHeap) -> list[int]:
    """The live keys of a heap, read from links, sorted plainly."""
    nodes: list[Node] = []
    for root in _circle_snapshot(heap._min):
        _descend(root, nodes)
    return sorted(node.key for node in nodes)
