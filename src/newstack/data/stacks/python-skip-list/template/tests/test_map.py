from __future__ import annotations

import bisect

import pytest

from {{ package_name }}.keys import SkipKeyValueError
from {{ package_name }}.map import SkipList, SkipListError

KEYS = list(range(-40, 41, 3))


def filled() -> SkipList:
    map_ = SkipList(seed=13)
    for index, key in enumerate(KEYS):
        map_.insert(key, index)
    return map_


def test_iteration_walks_the_sorted_order() -> None:
    assert list(filled().keys()) == sorted(KEYS)
    assert list(filled()) == sorted(KEYS)
    assert [value for _, value in filled().items()] == list(range(len(KEYS)))


def test_rank_answers_what_bisect_answers() -> None:
    map_ = filled()
    ordered = sorted(KEYS)
    for probe in range(-45, 45):
        assert map_.rank(probe) == bisect.bisect_left(ordered, probe)


def test_select_and_rank_are_exact_inverses() -> None:
    map_ = filled()
    for position in range(len(KEYS)):
        assert map_.rank(map_.select(position)[0]) == position


def test_a_repeat_replaces_the_value_not_the_slot() -> None:
    map_ = filled()
    edit = map_.insert(KEYS[3], "new")
    assert not edit.changed
    assert map_.get(KEYS[3]) == "new"
    assert len(map_) == len(KEYS)


def test_delete_unlinks_every_story_it_stood_on() -> None:
    map_ = filled()
    doomed = KEYS[::3]
    for key in doomed:
        assert map_.delete(key).changed
    survived = [key for key in sorted(KEYS) if key not in set(doomed)]
    assert len(map_) == len(survived)
    assert list(map_.keys()) == survived
    for probe in survived:
        assert map_.rank(probe) == bisect.bisect_left(survived, probe)


def test_a_second_delete_changes_nothing() -> None:
    map_ = filled()
    map_.delete(KEYS[0])
    assert not map_.delete(KEYS[0]).changed


def test_predecessor_and_successor_stop_at_the_ends() -> None:
    map_ = filled()
    assert map_.predecessor(min(KEYS)) is None
    assert map_.successor(max(KEYS)) is None
    assert map_.predecessor(KEYS[5]) == max(key for key in KEYS if key < KEYS[5])
    assert map_.successor(KEYS[5]) == min(key for key in KEYS if key > KEYS[5])


def test_a_window_holds_its_bounds() -> None:
    assert [key for key, _ in filled().window(-10, 10)] == [
        key for key in sorted(KEYS) if -10 <= key <= 10
    ]


def test_a_backwards_window_is_refused() -> None:
    with pytest.raises(SkipListError):
        filled().window(9, 3)


def test_a_position_past_the_map_is_refused() -> None:
    map_ = filled()
    with pytest.raises(SkipListError):
        map_.select(len(map_))
    with pytest.raises(SkipListError):
        map_.select(-1)
    with pytest.raises(SkipListError):
        map_.select("two")  # type: ignore[reportArgumentType]


def test_a_key_outside_the_order_is_refused() -> None:
    with pytest.raises(SkipKeyValueError):
        filled().insert([1], "no")


def test_stats_stay_within_the_log2_promise() -> None:
    stats = filled().stats()
    assert stats["size"] == len(KEYS)
    assert stats["tallest"] <= len(KEYS).bit_length() + 4
    assert stats["flips"] >= len(KEYS)
    assert sum(stats["levels"]) == len(KEYS)


def test_the_seed_owns_the_shape() -> None:
    left, right = filled(), filled()
    assert left.stats()["levels"] == right.stats()["levels"]
    assert left.rebuild().stats()["levels"] == left.stats()["levels"]
    assert left.rebuild().pairs() == left.pairs()


def test_the_map_prints_its_ladder() -> None:
    rows = filled().lines()
    assert rows[0].startswith("size")
    assert any("L0" in row for row in rows)
