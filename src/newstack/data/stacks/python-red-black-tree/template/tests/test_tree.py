from __future__ import annotations

import random

import pytest

from {{ package_name }}.tree import RBTree, TreeError

SEEDS = [50, 77, 12, 3, 91, 64, 21, 8, 45, 30]


def test_a_fresh_tree_is_empty_and_seated() -> None:
    tree = RBTree()
    assert tree.keys() == []
    assert tree.count() == 0
    assert tree.invariant()
    assert tree.audit() == []
    assert len(tree) == 0


def test_seeded_construction_walks_sorted() -> None:
    tree = RBTree(SEEDS)
    assert tree.keys() == sorted(SEEDS)
    assert tree.count() == len(SEEDS)
    assert tree.invariant()


def test_membership_answers_a_set() -> None:
    tree = RBTree(SEEDS)
    assert all(key in tree for key in SEEDS)
    assert 0 not in tree
    assert tree.has(50)
    assert not tree.has(7)


def test_insert_refuses_the_repeat() -> None:
    tree = RBTree(SEEDS)
    assert tree.insert(99) is True
    assert tree.insert(50) is False
    assert tree.count() == len(SEEDS) + 1


def test_a_storm_walks_sorted_after_every_op() -> None:
    rng = random.Random(9)
    tree = RBTree()
    live: set[int] = set()
    for _ in range(300):
        key = rng.randint(-90, 90)
        if rng.random() < 0.6 or not live:
            tree.insert(key)
            live.add(key)
        else:
            victim = rng.choice(sorted(live))
            tree.remove(victim)
            live.discard(victim)
        assert tree.keys() == sorted(live)
        assert tree.count() == len(live)
        assert tree.invariant()


def test_removal_of_an_absent_key_refuses() -> None:
    tree = RBTree(SEEDS)
    with pytest.raises(TreeError):
        tree.remove(7)
    assert tree.keys() == sorted(SEEDS)


def test_removal_keeps_the_walk_and_the_shape() -> None:
    tree = RBTree(SEEDS)
    for victim in [77, 50, 91, 8]:
        tree.remove(victim)
        assert tree.invariant()
    assert tree.keys() == sorted(set(SEEDS) - {77, 50, 91, 8})


def test_drop_min_walks_the_floor_off() -> None:
    tree = RBTree(SEEDS)
    order = sorted(SEEDS)
    for index, victim in enumerate(order):
        assert tree.drop_min() == victim
        assert tree.keys() == order[index + 1:]
        assert tree.invariant()
    with pytest.raises(TreeError):
        tree.drop_min()


def test_junk_never_enters_through_the_door() -> None:
    tree = RBTree([5])
    with pytest.raises(ValueError):
        tree.insert(1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tree.has("5")  # type: ignore[call-overload]
    assert tree.keys() == [5]


def test_a_rebuild_answers_identically() -> None:
    tree = RBTree(SEEDS)
    rebuilt = RBTree(tree.keys())
    assert rebuilt.keys() == tree.keys()
    assert rebuilt.count() == tree.count()
    assert rebuilt.invariant()


def test_iteration_walks_the_sorted_keys() -> None:
    tree = RBTree(SEEDS)
    assert list(tree) == sorted(SEEDS)
