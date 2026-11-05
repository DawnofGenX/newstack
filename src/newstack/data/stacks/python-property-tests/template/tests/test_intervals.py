"""The behaviour a reader expects, written as examples.

Examples are the wrong tool for the interesting cases (an overlap, a gap, a shared
bound) because people write the cases they already thought of. They stay here to
pin the documented contract; `test_properties.py` carries the invariants.
"""

from __future__ import annotations

import pytest

from {{ package_name }}.intervals import (
    Interval,
    coverage,
    expand,
    intersect,
    normalize,
    points_to_intervals,
    subtract,
)


def test_a_unit_interval_holds_one_point() -> None:
    assert Interval(3, 4).length == 1
    assert Interval(3, 4).contains(3)
    assert not Interval(3, 4).contains(4)


def test_an_empty_interval_is_allowed_but_normalised_away() -> None:
    assert Interval(2, 2).empty
    assert normalize([(2, 2)]) == []


def test_a_backwards_interval_is_a_programming_error() -> None:
    with pytest.raises(ValueError, match=r"5\.\.2 ends before it starts"):
        Interval(5, 2)


def test_touching_intervals_merge_into_one_run() -> None:
    assert normalize([(0, 1), (1, 2)]) == [Interval(0, 2)]


def test_a_one_point_gap_is_not_merged() -> None:
    assert normalize([(0, 1), (2, 3)]) == [Interval(0, 1), Interval(2, 3)]


def test_normalize_sorts_and_collapses() -> None:
    assert normalize([(4, 6), (0, 2), (1, 3), (0, 2)]) == [Interval(0, 3), Interval(4, 6)]


def test_coverage_counts_overlap_once() -> None:
    assert coverage([(0, 2), (1, 3)]) == 3
    assert coverage([(0, 2), (0, 2)]) == 2


def test_intersection_skips_touching_bounds() -> None:
    assert intersect([(0, 1)], [(1, 2)]) == []
    assert intersect([(0, 2), (4, 6)], [(1, 5)]) == [Interval(1, 2), Interval(4, 5)]


def test_subtraction_leaves_the_holes_empty() -> None:
    assert subtract([(0, 6)], [(2, 3)]) == [Interval(0, 2), Interval(3, 6)]
    assert subtract([(0, 4)], [(1, 9)]) == [Interval(0, 1)]


def test_points_become_runs() -> None:
    assert points_to_intervals([4, 1, 2, 3, 7]) == [Interval(1, 5), Interval(7, 8)]
    assert points_to_intervals([]) == []


def test_expand_is_the_inverse_of_coverage() -> None:
    assert list(expand([(0, 2), (2, 3)])) == [0, 1, 2]


def test_the_naive_sum_double_counts_an_overlap() -> None:
    from {{ package_name }}.cli import naive_coverage

    assert naive_coverage([Interval(0, 2), Interval(1, 3)]) == 4
    assert coverage([(0, 2), (1, 3)]) == 3
