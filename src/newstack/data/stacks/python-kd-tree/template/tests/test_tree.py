from __future__ import annotations

import random

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.points import PointError
from {{ package_name }}.tree import KDTree, distance, inside

SEEDS = (7, 23, 91, 1009)


def sample() -> KDTree:
    return KDTree([(5, 1), (2, 8), (9, 3), (5, 6), (-4, -4), (0, 0), (7, 7)])


def argmin(corpus: list[tuple[int, int]], probe: tuple[int, int]):
    return min(
        corpus,
        key=lambda p: ((p[0] - probe[0]) ** 2 + (p[1] - probe[1]) ** 2, p),
    )


def test_an_empty_tree_answers_what_it_is() -> None:
    empty = KDTree()
    assert list(empty) == []
    assert empty.walk() == []
    assert empty.count() == 0
    assert len(empty) == 0
    assert empty.audit() == []
    assert empty.invariant()
    assert not empty.has((0, 0))
    assert empty.range((-5, -5, 5, 5)) == []
    assert empty.nearest((0, 0)) is None


def test_a_lone_point_answers_for_itself() -> None:
    lone = KDTree([(3, 4)])
    assert lone.has((3, 4))
    assert not lone.has((3, 5))
    assert lone.nearest((0, 0)) == (3, 4)
    assert lone.range((-9, -9, 9, 9)) == [(3, 4)]
    assert list(lone) == [(3, 4)]
    assert lone.count() == 1


def test_a_doubled_point_is_seated_once() -> None:
    tree = sample()
    before = tree.count()
    assert tree.insert((5, 1)) is False
    assert tree.count() == before


def test_the_walk_holds_each_point_once() -> None:
    for seed in SEEDS:
        corpus = synthetic(80, seed=seed)
        tree = KDTree(corpus)
        assert sorted(tree.walk()) == sorted(set(corpus))
        assert list(tree) == sorted(set(corpus))
        assert tree.count() == len(set(corpus))


def test_membership_never_lies_after_interleaved_adds() -> None:
    for seed in SEEDS:
        corpus = synthetic(60, seed=seed)
        tree = KDTree()
        rng = random.Random(seed)
        for index, point in enumerate(corpus):
            tree.insert(point)
            if index % 2:
                tree.insert(corpus[rng.randrange(len(corpus))])
        seated = set(corpus)
        for _ in range(20):
            probe = (rng.randint(-400, 400), rng.randint(-400, 400))
            assert tree.has(probe) == (probe in seated)


def test_a_rectangle_answer_is_the_filter_on_every_corpus() -> None:
    for seed in SEEDS:
        corpus = synthetic(70, seed=seed)
        tree = KDTree(corpus)
        rng = random.Random(seed)
        for _ in range(10):
            low = (rng.randint(-400, 100), rng.randint(-400, 100))
            box = (low[0], low[1], low[0] + rng.randint(0, 300),
                   low[1] + rng.randint(0, 300))
            want = sorted(p for p in set(corpus) if inside(p, box))
            assert tree.range(box) == want


def test_a_box_crossing_a_split_walks_both_sides() -> None:
    tree = KDTree([(0, 0), (2, 2), (4, 4)])
    assert tree.range((1, 1, 3, 3)) == [(2, 2)]
    assert tree.range((-5, -5, 5, 5)) == [(0, 0), (2, 2), (4, 4)]
    assert tree.range((5, 5, 9, 9)) == []


def test_the_nearest_answer_is_the_argmin_on_every_corpus() -> None:
    for seed in SEEDS:
        corpus = synthetic(70, seed=seed)
        tree = KDTree(corpus)
        rng = random.Random(seed)
        for _ in range(15):
            probe = (rng.randint(-400, 400), rng.randint(-400, 400))
            assert tree.nearest(probe) == argmin(list(tree), probe)


def test_the_tie_goes_to_the_smallest_point() -> None:
    tree = KDTree([(1, 0), (0, 1)])
    assert tree.nearest((0, 0)) == (0, 1)
    twin = KDTree([(0, 1), (1, 0)])
    assert twin.nearest((0, 0)) == (0, 1)


def test_a_query_point_in_the_corpus_answers_itself() -> None:
    tree = sample()
    for point in [(-4, -4), (0, 0), (5, 1), (9, 3)]:
        assert tree.nearest(point) == point


def test_a_rebuilt_tree_answers_identically() -> None:
    for seed in SEEDS:
        corpus = synthetic(60, seed=seed)
        forward = KDTree(corpus)
        backward = KDTree(list(reversed(corpus)))
        assert list(forward) == list(backward)
        for probe in ((0, 0), (17, -23), (99, 99)):
            assert forward.has(probe) == backward.has(probe)
            assert forward.range((-50, -50, 50, 50)) == \
                backward.range((-50, -50, 50, 50))
            assert forward.nearest(probe) == backward.nearest(probe)


def test_equal_coordinates_walk_right() -> None:
    tree = KDTree([(5, 0), (5, 9), (5, 0)])
    assert tree.has((5, 9))
    assert list(tree) == [(5, 0), (5, 9)]


def test_distance_is_the_squared_hop() -> None:
    assert distance((0, 0), (3, 4)) == 25
    assert distance((2, 2), (2, 2)) == 0
    assert inside((2, 2), (2, 2, 2, 2))


def test_the_gate_refuses_every_half_point() -> None:
    tree = KDTree([(1, 2)])
    for bad in ((1.5, 2), (1, 2.0), (True, 1), (1,), "1,2", (1, 2, 3), None):
        with pytest.raises(PointError):
            tree.has(bad)
        with pytest.raises(PointError):
            tree.insert(bad)
        with pytest.raises(PointError):
            tree.nearest(bad)
