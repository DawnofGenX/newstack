from __future__ import annotations

import random

import pytest

from {{ package_name }}.points import PointError
from {{ package_name }}.scan import scan_has, scan_nearest, scan_range
from {{ package_name }}.tree import distance

CORPUS = [(5, 1), (2, 8), (9, 3), (5, 6), (-4, -4), (0, 0), (7, 7)]


def argmin(corpus, probe):
    return min(
        corpus,
        key=lambda p: ((p[0] - probe[0]) ** 2 + (p[1] - probe[1]) ** 2, p),
    )


def test_membership_walks_the_corpus_once() -> None:
    assert scan_has(CORPUS, (9, 3))
    assert not scan_has(CORPUS, (9, 4))
    assert not scan_has([], (0, 0))


def test_the_listing_is_sorted_even_when_the_corpus_is_not() -> None:
    shuffled = list(reversed(CORPUS))
    assert scan_range(shuffled, (-10, -10, 10, 10)) == sorted(CORPUS)
    assert scan_range(CORPUS, (50, 50, 60, 60)) == []
    assert scan_range(CORPUS, (0, 0, 0, 0)) == [(0, 0)]


def test_the_argmin_tie_goes_to_the_smallest_point() -> None:
    assert scan_nearest([(1, 0), (0, 1)], (0, 0)) == (0, 1)
    assert scan_nearest([(0, 1), (1, 0)], (0, 0)) == (0, 1)
    assert scan_nearest([], (0, 0)) is None


def test_the_scan_agrees_with_itself_under_reordering() -> None:
    rng = random.Random(11)
    corpus = [(rng.randint(-50, 50), rng.randint(-50, 50)) for _ in range(40)]
    shuffled = rng.sample(corpus, len(corpus))
    for _ in range(10):
        probe = (rng.randint(-60, 60), rng.randint(-60, 60))
        assert scan_nearest(corpus, probe) == scan_nearest(shuffled, probe)
        assert scan_range(corpus, (-20, -20, 20, 20)) == \
            scan_range(shuffled, (-20, -20, 20, 20))


def test_distance_ranks_the_argmin() -> None:
    for probe in ((0, 0), (3, -8)):
        for point in CORPUS:
            assert distance(point, probe) == \
                (point[0] - probe[0]) ** 2 + (point[1] - probe[1]) ** 2


@pytest.mark.parametrize("bad", [(1.5, 2), "1,2", None])
def test_the_scan_holds_the_gate(bad: object) -> None:
    with pytest.raises(PointError):
        scan_has(CORPUS, bad)
    with pytest.raises(PointError):
        scan_nearest(CORPUS, bad)
    with pytest.raises(PointError):
        scan_range(CORPUS, (bad, 0, 1, 1))
