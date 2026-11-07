from __future__ import annotations

import random
from dataclasses import FrozenInstanceError, replace

import pytest

from {{ package_name }}.check import holds, problems
from {{ package_name }}.keys import KeyError
from {{ package_name }}.node import (
    Node,
    blacken,
    delete,
    drop_min,
    insert,
    is_red,
    leaf,
    reddened,
    remove,
)

SEEDS = [50, 77, 12, 3, 91, 64, 21, 8, 45, 30]


def _build(seeds: list[int]):
    root = None
    for key in seeds:
        root = blacken(insert(root, key))
    return root


def walk(root) -> list[int]:
    if root is None:
        return []
    return [*walk(root.left), root.key, *walk(root.right)]


def test_nodes_are_immutable() -> None:
    node = leaf(5)
    with pytest.raises(FrozenInstanceError):
        node.key = 6
    recoloured = replace(node, color=0)
    assert recoloured.key == node.key


def test_a_bad_key_never_becomes_a_node() -> None:
    with pytest.raises(KeyError):
        Node(1.5)  # type: ignore[arg-type]


def test_insert_never_repeats_a_key() -> None:
    root = blacken(insert(None, 5))
    again = blacken(insert(root, 5))
    assert walk(again) == [5]


def test_the_walk_survives_every_insert() -> None:
    rng = random.Random(11)
    root = None
    live: set[int] = set()
    for _ in range(400):
        key = rng.randint(-120, 120)
        root = blacken(insert(root, key))
        live.add(key)
        assert walk(root) == sorted(live)
        assert holds(root)


def test_remove_of_a_held_key_keeps_the_promise() -> None:
    root = _build(SEEDS)
    for victim in [77, 50, 91, 8]:
        root = remove(root, victim)
        assert holds(root)
    assert walk(root) == sorted(set(SEEDS) - {77, 50, 91, 8})


def test_a_storm_of_removals_empties_in_order() -> None:
    root = _build(SEEDS)
    order = sorted(SEEDS)
    rng = random.Random(5)
    live = set(order)
    while live:
        victim = rng.choice(sorted(live))
        root = remove(root, victim)
        live.discard(victim)
        assert walk(root) == sorted(live)
        assert holds(root)


def test_delete_min_walks_the_leftmost_off() -> None:
    root = _build(SEEDS)
    smallest = min(SEEDS)
    root = drop_min(root)
    assert walk(root) == sorted(set(SEEDS) - {smallest})
    assert holds(root)


def test_delete_min_empties_a_storm() -> None:
    root = _build(SEEDS)
    order = sorted(SEEDS)
    for victim in order:
        assert root is not None
        root = drop_min(root)
        assert walk(root) == order[order.index(victim) + 1:]
    assert root is None


def test_reddened_and_blacken_frame_a_descent() -> None:
    root = _build(SEEDS)
    assert is_red(reddened(root)) or is_red(root.left) or is_red(root.right)
    assert not is_red(blacken(root))


def test_delete_assumes_a_reddened_root() -> None:
    root = _build(SEEDS)
    victim = max(SEEDS)
    cut = delete(reddened(root), victim)
    assert walk(cut) == sorted(set(SEEDS) - {victim})
    assert problems(blacken(cut)) == []
