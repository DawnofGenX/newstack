from __future__ import annotations

import pytest

from {{ package_name }} import simulate as subject
from {{ package_name }}.policies import (
    Decorrelated,
    EqualJitter,
    Exponential,
    Fixed,
    FullJitter,
)

SIM = subject.simulate


def test_a_fixed_delay_puts_every_client_in_one_bucket() -> None:
    result = SIM(Fixed(100.0), clients=50, seed=7, fail_ms=500.0, bucket_ms=10.0)
    assert result.peak_retries == 50
    assert result.peak_bucket_ms == 100
    # Five waves of the same size: one per retry, all 100 ms apart.
    assert result.buckets_used == 5
    assert set(result.per_bucket.values()) == {50}


def test_a_fixed_delay_keeps_retrying_until_the_outage_ends() -> None:
    result = SIM(Fixed(100.0), clients=50, seed=7, fail_ms=500.0)
    assert result.completed
    assert result.attempts == 50 * 6
    assert result.retries == 50 * 5


def test_exponential_still_waves_in_lockstep() -> None:
    result = SIM(Exponential(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    assert result.peak_retries == 200
    assert result.done_ms == 1_500
    assert result.buckets_used == 4


def test_full_jitter_spreads_the_wave() -> None:
    result = SIM(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    assert result.peak_retries < 60
    assert result.buckets_used > 100
    assert result.completed


def test_the_calm_policy_takes_longer() -> None:
    fixed = SIM(Fixed(100.0), clients=200, seed=7, fail_ms=1_000.0)
    jitter = SIM(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    assert jitter.done_ms > fixed.done_ms
    assert jitter.peak_retries < fixed.peak_retries


def test_equal_jitter_sits_between_full_jitter_and_backoff() -> None:
    equal = SIM(EqualJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    full = SIM(FullJitter(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    backoff = SIM(Exponential(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    assert full.peak_retries < equal.peak_retries < backoff.peak_retries


def test_the_same_seed_gives_the_same_curve() -> None:
    policy = FullJitter(100.0, 2.0, 1_000.0)
    first = SIM(policy, clients=120, seed=11, fail_ms=800.0)
    second = SIM(policy, clients=120, seed=11, fail_ms=800.0)
    third = SIM(policy, clients=120, seed=12, fail_ms=800.0)
    assert (first.peak_retries, first.retries, first.done_ms) == (
        second.peak_retries,
        second.retries,
        second.done_ms,
    )
    assert third.retries != first.retries


def test_the_first_attempt_is_not_a_retry() -> None:
    result = SIM(Fixed(100.0), clients=10, seed=7, fail_ms=200.0)
    assert result.attempts == result.clients + result.retries


def test_an_outage_shorter_than_one_attempt_settles_at_once() -> None:
    result = SIM(Fixed(100.0), clients=10, seed=7, fail_ms=0.0)
    assert result.retries == 0
    assert result.buckets_used == 0
    assert result.peak_retries == 0
    assert result.completed


def test_clients_out_of_attempts_are_reported_as_exhausted() -> None:
    result = SIM(Exponential(100.0, 2.0, 1_000.0), clients=10, fail_ms=100_000.0,
                 max_attempts=3)
    assert result.exhausted == 10
    assert not result.completed
    assert result.attempts == 30


def test_zero_clients_is_refused() -> None:
    with pytest.raises(subject.SimulationError, match="clients"):
        SIM(Fixed(), clients=0)


def test_a_zero_bucket_is_refused() -> None:
    with pytest.raises(subject.SimulationError, match="bucket"):
        SIM(Fixed(), bucket_ms=0.0)


def test_zero_attempts_is_refused() -> None:
    with pytest.raises(subject.SimulationError, match="attempt"):
        SIM(Fixed(), max_attempts=0)


def test_a_negative_outage_is_refused() -> None:
    with pytest.raises(subject.SimulationError, match="fail_ms"):
        SIM(Fixed(), fail_ms=-1.0)


def test_the_result_lines_name_the_peak_and_the_cost() -> None:
    result = SIM(FullJitter(100.0, 2.0, 1_000.0), clients=80, seed=5, fail_ms=600.0)
    text = "\n".join(result.lines())
    assert "peak" in text
    assert "settled" in text
    assert result.policy.startswith("full jitter")


def test_decorrelated_peaks_lower_than_exponential() -> None:
    decorrelated = SIM(Decorrelated(100.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    backoff = SIM(Exponential(100.0, 2.0, 1_000.0), clients=200, seed=7, fail_ms=1_000.0)
    assert decorrelated.peak_retries < backoff.peak_retries
    assert decorrelated.retries < backoff.retries
