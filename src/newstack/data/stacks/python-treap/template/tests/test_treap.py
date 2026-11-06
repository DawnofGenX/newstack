from __future__ import annotations

import bisect

import pytest

from {{ package_name }}.keys import KeyValueError
from {{ package_name }}.treap import Edit, Treap, TreapError

KEYS = list(range(-40, 41, 3))


def filled() -> Treap:
    tree = Treap(seed=13)
    for index, key in enumerate(KEYS):
        tree.insert(key, index)
    return tree


def test_iteration_walks_the_sorted_order() -> None:
    tree = filled()
    assert list(tree.keys()) == sorted(KEYS)
    assert list(tree) == sorted(KEYS)
    assert [value for _, value in tree.items()] == list(range(len(KEYS)))
    assert list(tree.values()) == list(range(len(KEYS)))


def test_rank_answers_what_bisect_answers() -> None:
    tree = filled()
    ordered = sorted(KEYS)
    for probe in range(-45, 45):
        assert tree.rank(probe) == bisect.bisect_left(ordered, probe)


def test_select_and_rank_are_exact_inverses() -> None:
    tree = filled()
    for position in range(len(KEYS)):
        assert tree.rank(tree.select(position)[0]) == position


def test_a_repeat_replaces_the_value_not_the_draw() -> None:
    tree = filled()
    before = tree.stats()["walk"]
    edit = tree.insert(KEYS[3], "new")
    assert not edit.changed
    assert tree.get(KEYS[3]) == "new"
    assert len(tree) == len(KEYS)
    assert tree.stats()["walk"] == before


def test_neither_order_breaks_under_a_mixed_storm() -> None:
    tree = Treap(seed=7)
    for index, key in enumerate(KEYS):
        tree.insert(key, index)
    for index, key in enumerate(KEYS[::2]):
        tree.delete(key)
        assert tree.stats()["broken"] == (0, 0)
        tree.insert(key * 7, index)
        assert tree.stats()["broken"] == (0, 0)


def test_split_holds_its_sides_and_the_join_restores() -> None:
    tree = filled()
    for pivot in (-40, -1, 0, 3, 40):
        under, over = tree.split(pivot)
        assert list(under.keys()) == [key for key in sorted(KEYS) if key < pivot]
        assert list(over.keys()) == [key for key in sorted(KEYS) if key >= pivot]
        joined = Treap.join(under, over)
        assert joined.pairs() == tree.pairs()
        assert joined.stats()["walk"] == tree.stats()["walk"]


def test_the_join_refuses_halves_that_overlap() -> None:
    tree = filled()
    with pytest.raises(TreapError):
        Treap.join(tree, tree)


def test_the_seed_owns_the_shape() -> None:
    left, right = Treap(seed=21), Treap(seed=21)
    for index, key in enumerate(KEYS):
        left.insert(key, index)
        right.insert(KEYS[-1 - index], index)
    assert left.stats()["walk"] == right.stats()["walk"]
    assert left.rebuild().stats()["walk"] == left.stats()["walk"]
    other = Treap(seed=22)
    for key, value in left.pairs():
        other.insert(key, value)
    assert other.pairs() == left.pairs()
    assert other.stats()["walk"] != left.stats()["walk"]


def test_delete_removes_and_the_halves_remerge() -> None:
    tree = filled()
    doomed = set(KEYS[::3])
    for key in doomed:
        assert tree.delete(key).changed
        assert tree.stats()["broken"] == (0, 0)
    survived = [key for key in sorted(KEYS) if key not in doomed]
    assert list(tree.keys()) == survived
    for probe in range(-45, 45):
        assert tree.rank(probe) == bisect.bisect_left(survived, probe)


def test_a_second_delete_changes_nothing() -> None:
    tree = filled()
    key = KEYS[4]
    tree.delete(key)
    edit = tree.delete(key)
    assert not edit.changed
    assert len(tree) == len(KEYS) - 1


def test_contains_and_get_refuse_nothing_and_find() -> None:
    tree = filled()
    assert tree.contains(KEYS[0])
    assert not tree.contains(KEYS[0] - 1)
    assert tree.get(KEYS[9]) == 9
    assert tree.get(12, "absent") == "absent"


def test_neighbours_stop_at_the_ends() -> None:
    tree = filled()
    assert tree.predecessor(min(KEYS)) is None
    assert tree.successor(max(KEYS)) is None
    assert tree.successor(min(KEYS)) == sorted(KEYS)[1]


def test_the_window_holds_its_bounds() -> None:
    tree = filled()
    assert [key for key, _ in tree.window(-10, 10)] == [
        key for key in sorted(KEYS) if -10 <= key <= 10
    ]
    with pytest.raises(TreapError):
        tree.window(10, -10)


def test_positions_outside_the_tree_are_refused() -> None:
    tree = filled()
    for position in (-1, len(KEYS), 1000, "two"):
        with pytest.raises(TreapError):
            tree.select(position)  # type: ignore[arg-type]


def test_a_key_outside_the_order_is_refused() -> None:
    tree = filled()
    with pytest.raises(KeyValueError):
        tree.insert([1, 2])  # type: ignore[arg-type]


def test_the_edit_reports_what_an_op_cost() -> None:
    tree = Treap(seed=1)
    edit = tree.insert(5, "five")
    assert isinstance(edit, Edit)
    assert edit.changed and edit.probes >= 1
    assert "insert" in edit.line()


def test_the_shape_stays_where_the_draws_promise() -> None:
    stats = filled().stats()
    assert stats["depth"] <= 2 * int(stats["expected_depth"]) + 4
    assert stats["draws"] >= len(KEYS)
    assert stats["broken"] == (0, 0)


def test_lines_describe_the_shape_without_lying() -> None:
    rows = filled().lines()
    assert rows[0].startswith("size 27")
    assert any(row.startswith("  d0") for row in rows)
