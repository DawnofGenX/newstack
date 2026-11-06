from __future__ import annotations

import bisect
from random import Random

import pytest

from {{ package_name }}.rules import depth_bound
from {{ package_name }}.tree import (
    ScapegoatTree,
    TreeError,
    _rebuild,
    flatten,
    height_of,
    size_of,
)

KEYS = list(range(-40, 41, 3))


def filled() -> ScapegoatTree:
    tree = ScapegoatTree()
    for index, key in enumerate(KEYS):
        tree.insert(key, index)
    return tree


def test_iteration_walks_the_sorted_order() -> None:
    tree = filled()
    assert list(tree.keys()) == sorted(KEYS)
    assert tree.pairs() == [(key, index) for index, key in enumerate(sorted(KEYS))]


def test_rank_answers_what_bisect_answers() -> None:
    tree = filled()
    ordered = sorted(KEYS)
    for probe in range(-45, 45):
        assert tree.rank(probe) == bisect.bisect_left(ordered, probe)


def test_select_and_rank_are_exact_inverses() -> None:
    tree = filled()
    for position in range(len(KEYS)):
        assert tree.rank(tree.select(position)[0]) == position


def test_a_repeat_replaces_the_value_not_the_tree() -> None:
    tree = filled()
    assert tree.insert(KEYS[3], "new") is False
    assert tree.get(KEYS[3]) == "new"
    assert len(tree) == len(KEYS)


def test_the_settled_tree_holds_the_rule_and_the_promise() -> None:
    tree = filled()
    assert tree.balanced()
    assert tree.depth() <= depth_bound(tree.alpha, len(tree))
    assert height_of(tree.root) == tree.depth()
    assert size_of(tree.root) == len(KEYS)


def test_a_mixed_storm_rechecks_the_rule_after_every_op() -> None:
    rng = Random(13)
    live: list[int] = []
    tree = ScapegoatTree()
    for _ in range(160):
        roll = rng.random()
        if roll < 0.45:
            key = rng.choice(KEYS)
            tree.insert(key, 1)
            live = sorted(set(live) | {key})
        elif roll < 0.65 and live:
            key = rng.choice(live)
            assert tree.delete(key)
            live = [x for x in live if x != key]
        else:
            key = rng.choice(KEYS)
            assert tree.rank(key) == bisect.bisect_left(live, key)
        if live:
            assert tree.balanced()
            assert [key for key, _ in flatten(tree.root)] == live
            assert tree.depth() <= depth_bound(tree.alpha, len(live))


def test_a_rebuild_is_lossless() -> None:
    tree = filled()
    stock = flatten(tree.root)
    rebuilt = ScapegoatTree()
    rebuilt.root = _rebuild(stock, 0, len(stock))
    assert flatten(rebuilt.root) == stock
    assert rebuilt.balanced()


def test_the_counter_charges_every_touch() -> None:
    tree = filled()
    before = tree.work
    tree.get(KEYS[0])
    assert tree.work > before


def test_positions_outside_the_tree_are_refused() -> None:
    tree = filled()
    for position in (-1, len(KEYS), 999):
        with pytest.raises(TreeError):
            tree.select(position)
    with pytest.raises(TreeError):
        tree.select(True)


def test_an_empty_tree_answers_quietly() -> None:
    tree = ScapegoatTree()
    assert tree.rank(5) == 0
    assert tree.delete(5) is False
    assert tree.depth() == 0
    assert tree.balanced()
    assert list(tree.keys()) == []


def test_delete_splices_without_losing_order() -> None:
    tree = filled()
    doomed = set(KEYS[::3])
    for key in doomed:
        assert tree.delete(key)
    survived = [key for key in sorted(KEYS) if key not in doomed]
    assert list(tree.keys()) == survived
    assert tree.balanced()
    for probe in range(-45, 45):
        assert tree.rank(probe) == bisect.bisect_left(survived, probe)
