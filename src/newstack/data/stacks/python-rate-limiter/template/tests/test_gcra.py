"""The arithmetic, without the lock: burst, refill, cost, and the exact retry time."""

from __future__ import annotations

import pytest

from {{ package_name }} import gcra as subject
from {{ package_name }} import model as model_mod


def state(limit: int, per_seconds: int, capacity: int):
    config = model_mod.Config(limit=limit, per_seconds=per_seconds, capacity=capacity)
    return subject.Gcra(config, 0)


def test_a_full_burst_is_admitted_then_refused() -> None:
    bucket = state(2, 1, 3)
    verdicts = [bucket.check("k", 0).allowed for _ in range(4)]
    assert verdicts == [True, True, True, False]


def test_remaining_counts_down_to_zero() -> None:
    bucket = state(2, 1, 3)
    assert [bucket.check("k", 0).remaining for _ in range(3)] == [2, 1, 0]


def test_the_retry_after_is_exactly_one_interval() -> None:
    bucket = state(2, 1, 3)
    for _ in range(3):
        bucket.check("k", 0)
    denied = bucket.check("k", 0)
    assert denied.retry_after_us == 500_000
    assert denied.retry_after_s == 0.5


def test_a_refill_only_happens_over_time() -> None:
    bucket = state(2, 1, 3)
    for _ in range(3):
        bucket.check("k", 0)
    assert not bucket.check("k", 499_999).allowed
    assert bucket.check("k", 500_000).allowed


def test_cost_is_spent_from_the_burst() -> None:
    bucket = state(1, 1, 3)
    assert bucket.check("k", 0, cost=3).allowed
    assert not bucket.check("k", 0).allowed


def test_a_cost_above_the_burst_is_refused() -> None:
    bucket = state(1, 1, 3)
    with pytest.raises(ValueError, match="exceeds the burst"):
        bucket.check("k", 0, cost=4)


def test_the_interval_is_exact_for_an_awkward_rate() -> None:
    bucket = state(7, 60, 7)
    assert bucket.interval == 60_000_000
    assert bucket.config.limit == 7
    for _ in range(7):
        bucket.check("k", 0)
    denied = bucket.check("k", 0)
    assert denied.retry_after_us == (60_000_000 + 6) // 7


def test_a_key_goes_idle_once_its_bucket_is_full_again() -> None:
    bucket = state(2, 1, 3)
    for _ in range(3):
        bucket.check("k", 0)
    assert not bucket.idle(0)
    assert not bucket.idle(1_000_000)
    assert bucket.idle(1_500_000)


def test_the_decision_line_is_greppable() -> None:
    bucket = state(1, 1, 1)
    assert bucket.check("user-1", 0).line() == "allow user-1       cost=1 remaining=0"
    denied = bucket.check("user-1", 0).line()
    assert denied.startswith("deny  user-1 ")
    assert "retry_after=1.000s" in denied
