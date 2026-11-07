"""Immutable nodes, honest links, and the fixup that re-seats them.

A node carries a key, a colour, and two children. Nothing is mutated:
every rotation, flip, insert, and delete hands back a new shape, so the
fixup preserves the in-order walk by construction and the checker in
``check.py`` can audit every result. Colours and ``is_red`` live with
the checker, their single authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .check import BLACK, RED, is_red
from .keys import ensure_key

__all__ = ["BLACK", "RED", "Node", "blacken", "delete", "delete_min",
           "insert", "is_red", "leaf"]


@dataclass(frozen=True)
class Node:
    """One key, one colour, two subtrees."""

    key: int
    color: int = RED
    left: Node | None = None
    right: Node | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", ensure_key(self.key))


def leaf(key: int) -> Node:
    """A fresh red leaf holding one key."""
    return Node(ensure_key(key), RED, None, None)


def blacken(root: Node | None) -> Node | None:
    """The root stands black; an empty tree stays empty."""
    return None if root is None else replace(root, color=BLACK)


def reddened(root: Node) -> Node:
    """Stand the root red for a descent when both shoulders are black."""
    if not is_red(root.left) and not is_red(root.right):
        return replace(root, color=RED)
    return root


def flip(node: Node) -> Node:
    """Turn the node's colour around and its children the other way."""
    left = node.left
    right = node.right
    return replace(
        node,
        color=1 - node.color,
        left=None if left is None else replace(left, color=1 - left.color),
        right=None if right is None else replace(right, color=1 - right.color),
    )


def rotate_left(node: Node) -> Node:
    """Lift the right child; the in-order walk is untouched."""
    right = node.right
    if right is None:
        return node
    lowered = replace(node, color=RED, right=right.left)
    return replace(right, color=node.color, left=lowered)


def rotate_right(node: Node) -> Node:
    """Lift the left child; the in-order walk is untouched."""
    left = node.left
    if left is None:
        return node
    lifted = replace(node, color=RED, left=left.right)
    return replace(left, color=node.color, right=lifted)


def balance(node: Node) -> Node:
    """The fixup: lean left, never two reds deep, colours paired."""
    if is_red(node.right) and not is_red(node.left):
        node = rotate_left(node)
    if is_red(node.left) and is_red(node.left.left):
        node = rotate_right(node)
    if is_red(node.left) and is_red(node.right):
        node = flip(node)
    return node


def push_left(node: Node) -> Node:
    """Push red past the left shoulder before a descent."""
    node = flip(node)
    right = node.right
    if right is not None and is_red(right.left):
        node = replace(node, right=rotate_right(right))
        node = flip(rotate_left(node))
    return node


def push_right(node: Node) -> Node:
    """Push red past the right shoulder before a descent."""
    node = flip(node)
    left = node.left
    if left is not None and is_red(left.left):
        node = flip(rotate_right(node))
    return node


def insert(node: Node | None, key: int) -> Node:
    """Place the key and re-seat every subtree the descent crossed."""
    if node is None:
        return leaf(key)
    if key < node.key:
        return balance(replace(node, left=insert(node.left, key)))
    if key > node.key:
        return balance(replace(node, right=insert(node.right, key)))
    return node


def delete_min(node: Node) -> Node | None:
    """Drop the leftmost key; the caller redened a black root."""
    if node.left is None:
        return None
    if not is_red(node.left) and not is_red(node.left.left):
        node = push_left(node)
    return balance(replace(node, left=delete_min(node.left)))


def drop_min(root: Node) -> Node | None:
    """Public descent: reddened on the way down, blacken on the way out."""
    return blacken(delete_min(reddened(root)))


def delete(node: Node, key: int) -> Node | None:
    """Remove a key known to sit in ``node``; the walk loses that key."""
    if key < node.key:
        left = node.left
        if left is None or (not is_red(left) and not is_red(left.left)):
            node = push_left(node)
        return balance(replace(node, left=delete(node.left, key)))
    if is_red(node.left):
        node = rotate_right(node)
    if node.right is None:
        return node.left
    right = node.right
    if not is_red(right) and (right.left is None or not is_red(right.left)):
        node = push_right(node)
    if key == node.key:
        successor = node.right
        while successor.left is not None:
            successor = successor.left
        return balance(replace(
            node, key=successor.key,
            right=delete_min(node.right),
        ))
    return balance(replace(node, right=delete(node.right, key)))


def remove(root: Node, key: int) -> Node | None:
    """Public descent: reddened on the way down, blacken on the way out."""
    return blacken(delete(reddened(root), key))
