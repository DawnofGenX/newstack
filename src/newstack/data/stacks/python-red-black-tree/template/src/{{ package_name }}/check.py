"""The checker: walks the tree and names every broken promise.

Root black, no red node fathers a red child, equal black height on
every root-to-leaf path, and ascending in-order keys: these are the
shape promises a red-black tree lives by, and the walk checks them in
plain sight: a red node never fathers a red node. ``problems`` is the
explicit walk every operation answers to; an empty list means the tree
still holds. Black heights count black nodes, null links sit at zero.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, breaks no cycle live
    from .node import Node

BLACK = 0
RED = 1


def is_red(node: Node | None) -> bool:
    """True when the node stands red; nothing stands black."""
    return node is not None and node.color == RED


def black_height(root: Node | None) -> int:
    """The black count down the leftmost path; nothing counts zero."""
    if root is None:
        return 0
    steps = 1 - root.color
    node = root.left
    while node is not None:
        steps += 1 - node.color
        node = node.left
    return steps


def edge_heights(root: Node | None) -> tuple[int, int]:
    """The black counts down the leftmost and rightmost paths."""
    if root is None:
        return 0, 0
    left, right = root.color == BLACK, root.color == BLACK
    node = root.left
    while node is not None:
        left += node.color == BLACK
        node = node.left
    node = root.right
    while node is not None:
        right += node.color == BLACK
        node = node.right
    return int(left), int(right)


def problems(root: Node | None) -> list[str]:
    """Every broken promise, named; an empty list means the tree holds.

    The walk is explicit and total: it visits every node, checks the
    colour against each child, counts black height on both sides, and
    pins each key between the bounds its ancestors allow.
    """
    issues: list[str] = []
    if root is not None and is_red(root):
        issues.append(f"root {root.key} stands red")
    _visit(root, None, None, issues)
    return issues


def _visit(node: Node | None, low: int | None, high: int | None,
           issues: list[str]) -> int:
    """Return the subtree's black height; report every split it breaks."""
    if node is None:
        return 0
    left = _visit(node.left, low, node.key, issues)
    right = _visit(node.right, node.key, high, issues)
    if left != right:
        issues.append(
            f"black heights split at {node.key}: {left} != {right}"
        )
    if is_red(node) and (is_red(node.left) or is_red(node.right)):
        issues.append(f"{node.key} fathers a red child")
    if low is not None and node.key <= low:
        issues.append(f"{node.key} sits at or below its floor {low}")
    if high is not None and node.key >= high:
        issues.append(f"{node.key} sits at or above its ceiling {high}")
    return left + (node.color == BLACK)


def holds(root: Node | None) -> bool:
    """True when the walk names nothing."""
    return not problems(root)
