from __future__ import annotations

import random

from {{ package_name }}.check import (
    BLACK,
    RED,
    black_height,
    edge_heights,
    holds,
    is_red,
    problems,
)
from {{ package_name }}.node import (
    Node,
    balance,
    blacken,
    insert,
    leaf,
)

FIVE = [5, 3, 9, 1, 4]


def _tree() -> Node:
    root: Node | None = None
    for key in FIVE:
        root = blacken(insert(root, key))
    assert root is not None
    return root


def test_is_red_treats_nothing_as_black() -> None:
    assert not is_red(None)
    assert is_red(Node(1, RED))
    assert not is_red(Node(1, BLACK))


def test_a_fresh_leaf_stands_red() -> None:
    assert is_red(leaf(7))


def test_black_height_counts_black_nodes() -> None:
    root = _tree()
    assert black_height(root) >= 1
    left, right = edge_heights(root)
    assert left == right


def test_an_empty_tree_counts_zero() -> None:
    assert black_height(None) == 0
    assert edge_heights(None) == (0, 0)
    assert holds(None)
    assert problems(None) == []


def test_a_balanced_shape_names_nothing() -> None:
    assert problems(_tree()) == []


def test_the_checker_names_a_red_root() -> None:
    broken = [word for word in problems(Node(4, RED)) if "red" in word]
    assert broken


def test_the_checker_names_a_red_father() -> None:
    broken = [word for word in problems(
        Node(5, BLACK, Node(3, RED, Node(2)))
    ) if "fathers" in word]
    assert broken


def test_the_checker_names_a_height_split() -> None:
    broken = [word for word in problems(
        Node(5, BLACK, Node(3, BLACK), None)
    ) if "split" in word]
    assert broken


def test_the_checker_names_a_broken_order() -> None:
    broken = [word for word in problems(
        Node(5, BLACK, Node(3), Node(7, RED, Node(4)))
    ) if "floor" in word or "ceiling" in word]
    assert broken


def test_balance_leans_left_and_pairs_colours() -> None:
    seeded = balance(Node(3, BLACK, None, Node(5, RED)))
    assert seeded.left is not None
    assert is_red(seeded.left)
    assert holds(blacken(seeded))


def test_a_storm_keeps_the_walk_sorted_under_balance() -> None:
    rng = random.Random(3)
    root: Node | None = None
    live: list[int] = []
    for _ in range(300):
        key = rng.randint(-80, 80)
        if key not in live:
            root = blacken(insert(root, key))
            live.append(key)
        assert holds(root)
    assert root is not None
