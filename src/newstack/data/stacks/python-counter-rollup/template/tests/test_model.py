from __future__ import annotations

import pytest

from {{ package_name }} import model as subject


def test_a_sample_refuses_a_bool_and_a_negative_value() -> None:
    with pytest.raises(subject.RollupError, match="at_us must be an integer"):
        subject.Sample(at_us=True, value=1)  # type: ignore[arg-type]
    with pytest.raises(subject.RollupError, match="value must be at least 0"):
        subject.Sample(at_us=0, value=-1)


def test_a_window_must_have_positive_width() -> None:
    with pytest.raises(subject.RollupError, match=r"window end 5 must be after its start 5"):
        subject.Window(start_us=5, end_us=5)
    assert subject.Window(0, 10).width_us == 10


def test_a_window_is_half_open() -> None:
    window = subject.Window(0, 10)
    assert window.contains(0)
    assert not window.contains(10)


def test_alignment_floors_to_the_window_start() -> None:
    assert subject.align(19_999_999, 10_000_000) == 10_000_000
    assert subject.align(20_000_000, 10_000_000) == 20_000_000
    assert subject.window_of(19_999_999, 10_000_000) == subject.Window(10_000_000, 20_000_000)


def test_a_seconds_width_becomes_microseconds() -> None:
    assert subject.seconds(2.5) == 2_500_000
    with pytest.raises(subject.RollupError, match="positive number of seconds"):
        subject.seconds(0)
    with pytest.raises(subject.RollupError, match="positive number of seconds"):
        subject.seconds(float("nan"))


def test_the_delta_of_two_readings_is_their_difference() -> None:
    assert subject.delta_for(subject.Sample(0, 10), subject.Sample(5, 25)) == (15, False)


def test_a_counter_that_went_down_is_a_restart_not_a_negative_delta() -> None:
    assert subject.delta_for(subject.Sample(0, 10), subject.Sample(5, 3)) == (3, True)


def test_readings_cannot_go_backwards() -> None:
    with pytest.raises(subject.RollupError, match="out of order"):
        subject.delta_for(subject.Sample(10, 1), subject.Sample(5, 2))


def test_a_rollup_with_one_interval_has_a_rate() -> None:
    piece = subject.Rollup(
        name="r", shard="s", window=subject.Window(0, 10), total=20,
        samples=1, resets=0, first_us=0, last_us=5_000_000,
    )
    assert piece.covered_us == 5_000_000
    assert piece.rate_per_second() == 4.0


def test_a_rollup_with_no_sampling_cannot_have_a_rate() -> None:
    piece = subject.Rollup(
        name="r", shard="s", window=subject.Window(0, 10), total=0,
        samples=0, resets=0, first_us=0, last_us=0,
    )
    with pytest.raises(subject.RollupError, match="the only honest rate is unknown, not zero"):
        piece.rate_per_second()
    assert "unknown" in piece.line()


def test_a_rollup_refuses_an_empty_name_and_a_backwards_span() -> None:
    with pytest.raises(subject.RollupError, match="name must not be empty"):
        subject.Rollup(name=" ", shard="s", window=subject.Window(0, 1), total=0,
                       samples=1, resets=0, first_us=0, last_us=1)
    with pytest.raises(subject.RollupError, match="is before the first"):
        subject.Rollup(name="r", shard="s", window=subject.Window(0, 1), total=0,
                       samples=1, resets=0, first_us=9, last_us=1)


def test_the_dict_carries_the_coverage_that_makes_the_rate_checkable() -> None:
    piece = subject.Rollup(name="r", shard="s", window=subject.Window(0, 10), total=20,
                           samples=1, resets=0, first_us=0, last_us=5_000_000)
    payload = piece.as_dict()
    assert payload["covered_us"] == 5_000_000
    assert payload["window"] == {"start_us": 0, "end_us": 10}
