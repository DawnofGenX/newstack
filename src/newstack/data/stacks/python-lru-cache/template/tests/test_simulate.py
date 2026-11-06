"""What a comparison reports, and what it refuses to claim."""

import pytest

from {{ package_name }} import simulate as subject
from {{ package_name }} import trace as trace_module


def test_a_comparison_returns_every_policy():
    results = subject.compare(trace_module.zipf_trace(2000), 50)
    assert [result.policy for result in results] == list(subject.POLICIES)


def test_every_row_counted_every_access():
    data = trace_module.zipf_trace(2000)
    assert all(result.accesses == len(data) for result in subject.compare(data, 50))


def test_no_policy_ever_beats_the_ceiling():
    data = trace_module.zipf_trace(4000)
    ceiling = subject.ceiling(data, 50)
    assert all(result.hit_rate <= ceiling + 1e-12 for result in subject.compare(data, 50))


def test_the_ceiling_is_the_share_of_the_hottest_keys():
    data = ["a", "a", "a", "b", "c"]
    assert subject.ceiling(data, 1) == pytest.approx(0.6)
    assert subject.ceiling(data, 2) == pytest.approx(0.8)
    assert subject.ceiling(data, 99) == pytest.approx(1.0)


def test_a_bigger_capacity_never_lowers_the_ceiling():
    data = trace_module.zipf_trace(2000)
    assert subject.ceiling(data, 100) >= subject.ceiling(data, 50)


def test_the_winner_is_the_best_row():
    results = subject.compare(trace_module.zipf_trace(2000), 50)
    assert subject.winner(results).hit_rate == max(result.hit_rate for result in results)


def test_a_loop_that_does_not_fit_is_zero_for_every_policy():
    data = trace_module.loop_trace(2000, 200)
    assert all(result.hit_rate == 0.0 for result in subject.compare(data, 150))


def test_the_same_loop_that_fits_misses_only_its_first_pass():
    data = trace_module.loop_trace(4000, 200)
    result = subject.run("lru", data, 200)
    assert result.hit_rate == pytest.approx((4000 - 200) / 4000)


def test_a_segmented_cache_survives_a_scan_better_than_an_lru():
    data = trace_module.scan_trace(6000, hot=50)
    lru = subject.run("lru", data, 100)
    slru = subject.run("slru", data, 100)
    assert slru.hit_rate > lru.hit_rate * 1.2


def test_clock_trails_lru_by_less_than_two_points():
    data = trace_module.zipf_trace(6000)
    gap = subject.run("lru", data, 100).hit_rate - subject.run("clock", data, 100).hit_rate
    assert 0.0 < gap < 0.02


def test_more_capacity_never_loses_hit_rate():
    data = trace_module.zipf_trace(4000)
    rates = [result.hit_rate for result in subject.capacity_curve(data, [10, 50, 200])]
    assert rates == sorted(rates)


def test_a_curve_returns_one_row_per_capacity():
    data = trace_module.zipf_trace(1000)
    curve = subject.capacity_curve(data, [10, 50, 200])
    assert [row.capacity for row in curve] == [10, 50, 200]


def test_an_empty_trace_is_refused():
    with pytest.raises(subject.SimulationError, match="no accesses"):
        subject.run("lru", [], 4)


def test_an_empty_comparison_is_refused():
    with pytest.raises(subject.SimulationError, match="nothing to compare"):
        subject.winner([])


def test_an_empty_curve_is_refused():
    with pytest.raises(subject.SimulationError, match="at least one capacity"):
        subject.capacity_curve(["a"], [])


def test_a_zero_capacity_in_a_curve_is_refused():
    with pytest.raises(subject.SimulationError, match="at least 1"):
        subject.capacity_curve(["a"], [0])


def test_the_ceiling_refuses_a_zero_capacity():
    with pytest.raises(subject.SimulationError, match="at least 1"):
        subject.ceiling(["a"], 0)


def test_the_row_line_holds_the_policy_and_the_rate():
    result = subject.run("lru", trace_module.zipf_trace(500), 20)
    line = result.line()
    assert line.startswith("lru")
    assert f"{result.hit_rate:.4f}" in line


def test_the_header_names_every_column():
    header = subject.header()
    for column in ("policy", "capacity", "hit rate", "evictions", "scans", "promotions"):
        assert column in header
