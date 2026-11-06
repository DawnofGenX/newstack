from __future__ import annotations

import random

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.scan import scan_overlap, scan_stab
from {{ package_name }}.span import Interval
from {{ package_name }}.tree import IntervalTree, TreeError

SEEDS = (7, 23, 91, 1009)


def tree() -> IntervalTree:
    return IntervalTree([Interval(1, 5), Interval(3, 9), Interval(5, 6), Interval(8, 12)])


def test_a_fresh_tree_is_empty_but_answering() -> None:
    empty = IntervalTree()
    assert empty.walk() == []
    assert empty.stab(0) == []
    assert empty.overlap(-9, 9) == []
    assert empty.first(0) is None
    assert len(empty) == 0
    assert empty.height == 0
    assert empty.audit() == []
    assert empty.delete(Interval(0, 1)) is False


def test_the_walk_is_the_sorted_corpus() -> None:
    spans = synthetic(50, seed=3, low=-90, high=90)
    found = IntervalTree(spans)
    assert found.walk() == sorted(spans)
    assert list(found) == sorted(spans)
    assert len(found) == len(set(spans))


def test_stabbing_skips_nothing_and_invents_nothing() -> None:
    for seed in SEEDS:
        spans = synthetic(90, seed=seed, low=-150, high=150)
        found = IntervalTree(spans)
        rng = random.Random(seed * 13)
        for _ in range(50):
            point = rng.randrange(-160, 160)
            assert found.stab(point) == scan_stab(spans, point)


def test_overlap_skips_nothing_and_invents_nothing() -> None:
    for seed in SEEDS:
        spans = synthetic(90, seed=seed, low=-150, high=150)
        found = IntervalTree(spans)
        rng = random.Random(seed * 17)
        for _ in range(40):
            low = rng.randrange(-160, 140)
            high = low + rng.randrange(1, 70)
            assert found.overlap(low, high) == scan_overlap(spans, low, high)


def test_a_point_at_an_end_stands_outside() -> None:
    found = tree()
    assert found.stab(5) == [Interval(3, 9), Interval(5, 6)]
    assert found.stab(9) == [Interval(8, 12)]
    assert IntervalTree([Interval(1, 3), Interval(3, 5)]).stab(3) == [Interval(3, 5)]
    assert IntervalTree([Interval(1, 3)]).overlap(3, 5) == []


def test_first_answers_the_earliest_holder() -> None:
    found = tree()
    assert found.first(4) == Interval(1, 5)
    assert found.first(100) is None


def test_insert_lands_once_and_delete_walks_the_heights() -> None:
    found = IntervalTree()
    assert found.insert(Interval(2, 9)) is True
    assert found.insert(Interval(2, 9)) is False
    assert len(found) == 1
    assert found.delete(Interval(2, 9)) is True
    assert found.delete(Interval(2, 9)) is False
    assert found.walk() == []
    with pytest.raises(TreeError):
        found.insert((2, 9))  # type: ignore[arg-type]


def test_the_augmentation_survives_every_delete() -> None:
    for seed in SEEDS:
        spans = synthetic(70, seed=seed, low=-80, high=80)
        found = IntervalTree(spans)
        shelf = list(spans)
        rng = random.Random(seed * 19)
        while shelf:
            doomed = rng.choice(shelf)
            assert found.delete(doomed) is True
            shelf.remove(doomed)
            assert found.audit() == []
            point = rng.randrange(-80, 80)
            assert found.stab(point) == scan_stab(shelf, point)
        assert found.walk() == []


def test_a_shallow_root_survives_its_neighbours() -> None:
    spans = [Interval(0, 100), Interval(1, 2), Interval(3, 4), Interval(5, 6)]
    found = IntervalTree(spans)
    assert found.delete(Interval(0, 100)) is True
    assert found.stab(5) == [Interval(5, 6)]
    assert found.audit() == []
    assert found.delete(Interval(5, 6)) is True
    assert found.stab(5) == []
    assert found.overlap(0, 7) == [Interval(1, 2), Interval(3, 4)]
    assert found.audit() == []


def test_an_empty_window_question_is_refused() -> None:
    found = tree()
    with pytest.raises(TreeError):
        found.overlap(9, 3)
    with pytest.raises(TreeError):
        found.overlap(4, 4)
    with pytest.raises(TreeError):
        found.stab("four")  # type: ignore[arg-type]


def test_deep_corporas_stay_audited() -> None:
    found = IntervalTree(synthetic(400, seed=31, low=-2000, high=2000, widest=120))
    assert found.audit() == []
    assert found.height >= 6
