from __future__ import annotations

import pytest
from support import MICROSECONDS, readings

from {{ package_name }} import rollup as subject


def test_each_interval_lands_in_the_window_of_its_later_reading() -> None:
    width = 10 * MICROSECONDS
    pieces = subject.rollup(readings([(0, 0), (10, 100), (20, 200), (30, 300)]), width, name="r")
    assert [piece.window.start_us // MICROSECONDS for piece in pieces] == [10, 20, 30]
    assert [piece.total for piece in pieces] == [100, 100, 100]


def test_the_reading_at_zero_is_a_level_not_a_rate() -> None:
    pieces = subject.rollup(readings([(0, 7)]), 10 * MICROSECONDS, name="r")
    assert pieces == []


def test_a_steady_counter_reports_the_rate_it_ran_at() -> None:
    pieces = subject.rollup(readings([(0, 0), (10, 100), (20, 200)]), 10 * MICROSECONDS, name="r")
    assert [round(piece.rate_per_second(), 6) for piece in pieces] == [10.0, 10.0]


def test_a_restart_is_the_new_value_and_a_reset_count() -> None:
    width = 10 * MICROSECONDS
    pieces = subject.rollup(readings([(0, 500), (10, 600), (20, 20), (30, 120)]), width, name="r")
    assert [piece.total for piece in pieces] == [100, 20, 100]
    assert [piece.resets for piece in pieces] == [0, 1, 0]
    assert pieces[1].rate_per_second() == 2.0


def test_an_interval_that_straddles_a_boundary_belongs_to_the_later_window() -> None:
    pieces = subject.rollup(readings([(0, 0), (25, 50)]), 10 * MICROSECONDS, name="r")
    assert len(pieces) == 1
    assert pieces[0].window.start_us == 20 * MICROSECONDS
    assert pieces[0].covered_us == 25 * MICROSECONDS
    assert pieces[0].rate_per_second() == 2.0


def test_a_missing_window_is_absent_not_zero() -> None:
    pieces = subject.rollup(
        readings([(0, 0), (10, 10), (20, 20), (40, 40), (50, 50)]), 10 * MICROSECONDS, name="r"
    )
    assert [piece.window.start_us // MICROSECONDS for piece in pieces] == [10, 20, 40, 50]
    holes = subject.gaps(pieces, 10 * MICROSECONDS)
    assert [hole.start_us // MICROSECONDS for hole in holes] == [30]


def test_gaps_need_two_windows_to_exist_between() -> None:
    one = subject.rollup(readings([(0, 0), (10, 1)]), 10 * MICROSECONDS, name="r")
    assert subject.gaps(one, 10 * MICROSECONDS) == []


def test_the_rate_divides_by_observed_time_not_by_window_count() -> None:
    pieces = subject.rollup(
        readings([(0, 0), (10, 10), (20, 20), (40, 40), (50, 50)]), 10 * MICROSECONDS, name="r"
    )
    # The interval that spans the missing window still covers 20 s of observation,
    # so the denominator is 50 s and the answer is 1.0/s, not 60/40 or 50/40.
    assert subject.rate_per_second(pieces) == pytest.approx(1.0)


def test_no_coverage_has_no_rate() -> None:
    with pytest.raises(subject.RollupError, match="unknown, not zero"):
        subject.rate_per_second([])


def test_out_of_order_readings_are_refused_rather_than_sorted() -> None:
    with pytest.raises(subject.RollupError, match="out of order"):
        subject.rollup([readings([(10, 1)])[0], readings([(0, 2)])[0]], 10 * MICROSECONDS, name="r")


def test_a_jsonl_line_becomes_a_sample() -> None:
    sample = subject.parse_line(1, '{"at_us": 5, "value": 9}')
    assert (sample.at_us, sample.value) == (5, 9)
    with pytest.raises(subject.RollupError, match="line 2 is not JSON"):
        subject.parse_line(2, "{")
    with pytest.raises(subject.RollupError, match="is missing 'value'"):
        subject.parse_line(3, '{"at_us": 1}')
    with pytest.raises(subject.RollupError, match="line 4 is not an object"):
        subject.parse_line(4, "[]")
