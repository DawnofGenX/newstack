"""The truth side: the same percentile rule, and the average trap."""

import pytest

from {{ package_name }} import histogram as hist
from {{ package_name }} import stats as subject


def build(values, bits=hist.DEFAULT_SIGNIFICANT_BITS):
    histogram = hist.Histogram(bits)
    histogram.record_many(values)
    return histogram


def test_nearest_rank_is_one_based():
    values = list(range(1, 101))
    assert subject.nearest_rank(values, 50) == 50
    assert subject.nearest_rank(values, 1) == 1
    assert subject.nearest_rank(values, 100) == 100


def test_nearest_rank_rounds_up():
    assert subject.nearest_rank([10, 20, 30], 50) == 20


def test_nearest_rank_of_nothing_is_refused():
    with pytest.raises(subject.StatsError, match="no samples"):
        subject.nearest_rank([], 50)


@pytest.mark.parametrize("point", [0, 101])
def test_an_impossible_percentile_is_refused(point):
    with pytest.raises(subject.StatsError, match="percentile"):
        subject.nearest_rank([1, 2], point)


def test_the_mean_of_nothing_is_refused():
    with pytest.raises(subject.StatsError):
        subject.mean([])


def test_the_check_holds_when_the_histogram_keeps_its_promise():
    values = [7, 70, 700, 7000, 70_000]
    compared = subject.check(build(values), values, points=(50.0, 99.0))
    assert compared.held()
    assert compared.samples == 5
    assert compared.worst <= compared.promised


def test_the_check_refuses_a_histogram_of_a_different_size():
    with pytest.raises(subject.StatsError, match="sample"):
        subject.check(build([1, 2]), [1])


def test_every_row_carries_the_three_numbers():
    values = [10, 1000, 100_000]
    compared = subject.check(build(values), values, points=(100.0,))
    row = compared.rows[0]
    assert row.reported >= row.truth
    assert "reported" in row.line()
    assert "gap" in row.line()


def test_the_average_of_one_group_is_that_group():
    assert subject.average_of_percentiles([{"p99": 42.0}], "p99") == 42.0


def test_the_average_of_two_groups_is_between_them():
    averaged = subject.average_of_percentiles([{"p99": 10.0}, {"p99": 30.0}], "p99")
    assert averaged == 20.0


def test_averaging_nothing_is_refused():
    with pytest.raises(subject.StatsError):
        subject.average_of_percentiles([], "p99")


def test_the_pooled_percentile_sees_every_sample():
    assert subject.pooled_percentile([[1, 2, 3], [4, 5, 6]], 50) == 3
    assert subject.pooled_percentile([[1, 2, 3], [4, 5, 6]], 95) == 6


def test_a_byte_cost_needs_a_sample():
    with pytest.raises(subject.StatsError):
        subject.bytes_per_sample(build([1]), 0)


def test_the_byte_cost_falls_as_samples_are_added():
    histogram = build(range(1, 1001))
    assert subject.bytes_per_sample(histogram, 1000) > subject.bytes_per_sample(histogram, 100_000)
