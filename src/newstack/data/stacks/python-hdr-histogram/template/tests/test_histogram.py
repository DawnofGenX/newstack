"""The layout, the promise, and the merge."""

import pytest

from {{ package_name }} import histogram as subject


def filled(values, bits=subject.DEFAULT_SIGNIFICANT_BITS):
    histogram = subject.Histogram(bits)
    histogram.record_many(values)
    return histogram


def test_a_small_value_is_exact():
    assert subject.width_of(subject.index_of(83)) == 1


def test_the_first_bucket_above_the_exact_range_holds_two_values():
    assert subject.width_of(subject.index_of(2048)) == 2


def test_the_index_is_monotone():
    indexes = [subject.index_of(value) for value in (0, 1, 1024, 2048, 4096, 1 << 20)]
    assert indexes == sorted(indexes)
    assert len(set(indexes)) == len(indexes)


def test_floor_and_ceiling_bracket_the_value():
    for value in (1, 1023, 1024, 2048, 2049, 123_456, 987_654):
        index = subject.index_of(value)
        assert subject.floor_of(index) <= value <= subject.ceiling_of(index)


def test_the_relative_width_never_exceeds_the_promise():
    for value in (2048, 3000, 19_999, 250_000, 4_000_000):
        index = subject.index_of(value)
        width = subject.width_of(index)
        assert width / subject.floor_of(index) <= subject.relative_error(10) + 1e-12


def test_more_bits_means_a_narrower_bucket():
    assert subject.width_of(subject.index_of(250_000, 14), 14) < subject.width_of(
        subject.index_of(250_000, 10)
    )


def test_the_promised_error_is_one_over_the_sub_bucket_count():
    assert subject.relative_error(6) == pytest.approx(1 / 64)
    assert subject.relative_error(10) == pytest.approx(1 / 1024)


@pytest.mark.parametrize("bits", [0, 17, -1])
def test_an_impossible_resolution_is_refused(bits):
    with pytest.raises(subject.HistogramError):
        subject.Histogram(bits)


def test_a_bool_resolution_is_refused():
    with pytest.raises(subject.HistogramError, match="whole number"):
        subject.Histogram(True)


def test_a_negative_latency_is_refused():
    with pytest.raises(subject.HistogramError, match="negative"):
        subject.Histogram().record(-5)


def test_a_non_integer_latency_is_refused():
    with pytest.raises(subject.HistogramError, match="whole number"):
        subject.Histogram().record(2.0)  # type: ignore[arg-type]


def test_the_count_and_the_sum_are_exact():
    histogram = filled([5, 10, 15, 2000])
    assert histogram.count() == 4
    assert histogram.total_sum == 2030
    assert histogram.mean() == pytest.approx(507.5)


def test_the_minimum_is_exact():
    assert filled([900, 3, 7000]).lowest == 3


def test_the_mean_of_nothing_is_refused():
    with pytest.raises(subject.HistogramError, match="no samples"):
        subject.Histogram().mean()


def test_a_percentile_never_reports_below_the_truth():
    values = list(range(1, 2001))
    histogram = filled(values)
    for point in (1, 25, 50, 90, 99, 100):
        truth = sorted(values)[max(0, -(-point * len(values) // 100) - 1)]
        assert histogram.percentile(point) >= truth


def test_the_median_of_an_odd_sample_is_the_middle_value():
    histogram = filled(list(range(1, 101)))
    assert histogram.percentile(50) >= 50
    assert histogram.percentile(50) <= 51


@pytest.mark.parametrize("point", [0, -1, 100.5])
def test_an_impossible_percentile_is_refused(point):
    with pytest.raises(subject.HistogramError, match="percentile"):
        filled([1, 2, 3]).percentile(point)


def test_a_percentile_of_nothing_is_refused():
    with pytest.raises(subject.HistogramError, match="no samples"):
        subject.Histogram().percentile(50)


def test_a_rank_outside_the_sample_is_refused():
    with pytest.raises(subject.HistogramError, match="rank"):
        filled([1, 2, 3]).value_at_rank(4)


def test_the_bucket_count_covers_the_values_that_arrived():
    histogram = filled(list(range(1, 5001)))
    assert 0 < histogram.buckets_used <= histogram.count()


def test_the_byte_cost_follows_the_range_not_the_sample_count():
    small = filled(list(range(1, 101)))
    large = filled(list(range(1, 101)) * 1000)
    assert small.bytes_used == large.bytes_used
    assert small.buckets_used == large.buckets_used


def test_a_wider_range_costs_more_bytes():
    assert filled(range(1, 100_000)).bytes_used > filled(range(1, 100)).bytes_used


def test_a_value_past_the_layout_is_refused():
    histogram = subject.Histogram(10, max_value=1000)
    with pytest.raises(subject.HistogramError, match="past that"):
        histogram.record(100_000)


def test_merging_adds_the_buckets():
    left, right = filled([1, 2, 3]), filled([3, 4, 5])
    merged = left.merged(right)
    assert merged.count() == 6
    assert merged.total_sum == 18
    assert merged.as_dict()["counts"] == filled([1, 2, 3, 3, 4, 5]).as_dict()["counts"]


def test_merging_across_layouts_is_refused():
    with pytest.raises(subject.HistogramError, match="bucket boundaries"):
        filled([1], 10).merged(filled([1], 12))


def test_a_dictionary_round_trips():
    histogram = filled([1, 2048, 500_000])
    assert subject.parse_histogram(histogram.as_dict()).as_dict() == histogram.as_dict()


def test_a_foreign_dictionary_is_refused():
    with pytest.raises(subject.HistogramError, match="not a histogram"):
        subject.parse_histogram({"type": "count-min-sketch"})


def test_a_dictionary_needs_a_whole_number_resolution():
    with pytest.raises(subject.HistogramError, match="significant_bits"):
        subject.parse_histogram({"type": "hdr-histogram", "significant_bits": "ten"})


def test_a_dictionary_with_unreadable_counters_is_refused():
    payload = {"type": "hdr-histogram", "significant_bits": 10, "counts": [1, 2]}
    with pytest.raises(subject.HistogramError, match="counters"):
        subject.parse_histogram(payload)


def test_a_total_that_contradicts_the_counters_is_refused():
    payload = {"type": "hdr-histogram", "significant_bits": 10, "counts": {"1": 2}, "total": 5}
    with pytest.raises(subject.HistogramError, match="add up"):
        subject.parse_histogram(payload)
