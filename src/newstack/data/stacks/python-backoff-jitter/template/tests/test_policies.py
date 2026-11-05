from __future__ import annotations

import itertools

import pytest

from {{ package_name }} import policies as subject
from {{ package_name }}.rng import Rng
from {{ package_name }}.simulate import decreases, delay_series

Fixed = subject.Fixed
Exponential = subject.Exponential
FullJitter = subject.FullJitter
EqualJitter = subject.EqualJitter
Decorrelated = subject.Decorrelated


def test_fixed_ignores_the_attempt_number() -> None:
    policy = Fixed(250.0)
    assert [policy.delay_ms(Rng(1), attempt) for attempt in (1, 7, 20)] == [250.0, 250.0, 250.0]


def test_exponential_doubles_until_the_cap() -> None:
    policy = Exponential(100.0, 2.0, 800.0)
    assert [policy.ceiling(attempt) for attempt in (1, 2, 3, 4, 5)] == [
        100.0,
        200.0,
        400.0,
        800.0,
        800.0,
    ]


def test_full_jitter_draws_below_the_ceiling() -> None:
    policy = FullJitter(100.0, 2.0, 1_000.0)
    stream = Rng(4)
    for attempt in range(1, 12):
        delay = policy.delay_ms(stream, attempt)
        assert 0.0 <= delay <= policy.ceiling(attempt)


def test_full_jitter_does_not_repeat_one_number() -> None:
    policy = FullJitter(100.0, 2.0, 1_000.0)
    stream = Rng(4)
    draws = {round(policy.delay_ms(stream, 1), 6) for _ in range(50)}
    assert len(draws) > 20


def test_equal_jitter_keeps_the_lower_half() -> None:
    policy = EqualJitter(100.0, 2.0, 1_000.0)
    stream = Rng(4)
    draws = [policy.delay_ms(stream, 1) for _ in range(100)]
    ceiling = policy.ceiling(1)
    assert all(ceiling / 2 <= delay <= ceiling for delay in draws)
    assert len({round(draw, 6) for draw in draws}) > 20


def test_decorrelated_stays_under_its_cap() -> None:
    series = delay_series(Decorrelated(100.0, 1_000.0), seed=2, count=40)
    assert max(series) <= 1_000.0
    assert min(series) >= 100.0


def test_decorrelated_counts_its_decreases() -> None:
    series = delay_series(Decorrelated(100.0, 1_000.0), seed=2, count=40)
    counted = sum(1 for earlier, later in itertools.pairwise(series) if later < earlier)
    assert decreases(series) == counted
    assert counted > 0


def test_a_zero_delay_is_refused() -> None:
    with pytest.raises(subject.PolicyError, match="positive"):
        Fixed(0.0)


def test_a_shrinking_factor_is_refused() -> None:
    with pytest.raises(subject.PolicyError, match="factor"):
        Exponential(100.0, 0.5)


def test_a_cap_below_the_base_is_refused() -> None:
    with pytest.raises(subject.PolicyError, match="cap"):
        Decorrelated(1_000.0, 100.0)


def test_an_unknown_name_lists_the_known_ones() -> None:
    with pytest.raises(subject.PolicyError) as caught:
        subject.by_name("magic")
    assert "magic" in str(caught.value)
    assert "full-jitter" in str(caught.value)


def test_every_known_policy_builds_and_describes_itself() -> None:
    for name, factory in subject.POLICIES.items():
        policy = factory()
        assert policy.name == name
        assert policy.describe()
