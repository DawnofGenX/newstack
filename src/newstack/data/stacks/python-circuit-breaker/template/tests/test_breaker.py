"""The state machine, one rule per test."""

from __future__ import annotations

import pytest

from {{ package_name }} import breaker as subject
from {{ package_name }} import clock as clock_mod
from {{ package_name }} import model as model_mod


def test_a_closed_breaker_allows_everything(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=3)
    assert breaker.allow().allowed is True
    assert breaker.state is model_mod.State.CLOSED


def test_consecutive_failures_trip_it(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=3)
    for _ in range(2):
        breaker.record_failure(RuntimeError("503"))
    assert breaker.state is model_mod.State.CLOSED
    breaker.record_failure(RuntimeError("503"))
    assert breaker.state is model_mod.State.OPEN
    assert breaker.tally.trips == 1


def test_a_success_resets_the_count(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=3)
    breaker.record_failure(RuntimeError("503"))
    breaker.record_failure(RuntimeError("503"))
    breaker.record_success()
    assert breaker.consecutive_failures == 0
    breaker.record_failure(RuntimeError("503"))
    assert breaker.state is model_mod.State.CLOSED


def test_a_single_failure_can_trip_a_strict_breaker(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=1)
    breaker.record_failure(RuntimeError("503"))
    assert breaker.state is model_mod.State.OPEN


def test_open_refuses_before_calling_anything(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=1)
    breaker.record_failure(RuntimeError("503"))
    calls: list[int] = []
    with pytest.raises(model_mod.OpenError) as caught:
        breaker.call(lambda: calls.append(1))
    assert calls == []
    assert caught.value.retry_in == subject.DEFAULT_COOLDOWN_S


def test_retry_in_counts_down(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=30.0)
    breaker.record_failure(RuntimeError("503"))
    assert breaker.retry_in() == 30.0
    clock.advance(12.5)
    assert breaker.retry_in() == 17.5
    decision = breaker.allow()
    assert decision.allowed is False
    assert decision.retry_in == 17.5


def test_the_cooldown_admits_exactly_one_probe(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=10.0)
    breaker.record_failure(RuntimeError("503"))
    clock.advance(10.0)
    first = breaker.allow()
    assert first.allowed is True
    assert first.state is model_mod.State.HALF_OPEN
    second = breaker.allow()
    assert second.allowed is False
    assert "already in flight" in second.reason
    assert breaker.tally.probes == 1
    assert breaker.tally.denied == 1


def test_a_successful_probe_closes_it(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=10.0)
    breaker.record_failure(RuntimeError("503"))
    clock.advance(10.0)
    breaker.call(lambda: "ok")
    assert breaker.state is model_mod.State.CLOSED
    assert breaker.tally.successes == 1


def test_a_failed_probe_restarts_the_cooldown(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=10.0)
    breaker.record_failure(RuntimeError("503"))
    clock.advance(10.0)
    breaker.allow()
    breaker.record_failure(RuntimeError("still down"))
    assert breaker.state is model_mod.State.OPEN
    assert breaker.retry_in() == 10.0
    assert breaker.tally.trips == 2


def test_two_probe_successes_can_be_required(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=5.0, half_open_successes=2)
    breaker.record_failure(RuntimeError("503"))
    clock.advance(5.0)
    assert breaker.allow().allowed is True
    breaker.record_success()
    assert breaker.state is model_mod.State.HALF_OPEN
    assert breaker.allow().allowed is True
    breaker.record_success()
    assert breaker.state is model_mod.State.CLOSED


def test_an_ignored_error_is_not_an_outage(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=1, ignore=(ValueError,))
    assert breaker.record_failure(ValueError("422")) is False
    assert breaker.state is model_mod.State.CLOSED
    assert breaker.tally.ignored == 1
    assert breaker.record_failure(RuntimeError("503")) is True
    assert breaker.state is model_mod.State.OPEN


def test_an_ignored_probe_failure_releases_the_probe(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=1.0, ignore=(ValueError,))
    breaker.record_failure(RuntimeError("503"))
    clock.advance(1.0)
    assert breaker.allow().allowed is True
    breaker.record_failure(ValueError("422"))
    assert breaker.state is model_mod.State.HALF_OPEN
    assert breaker.allow().allowed is True


def test_a_straggler_does_not_extend_the_outage(make_breaker, clock) -> None:
    breaker = make_breaker(failure_threshold=1, cooldown_s=10.0)
    breaker.record_failure(RuntimeError("503"))
    breaker.record_failure(RuntimeError("slow 503 from before the trip"))
    assert breaker.tally.late == 1
    assert breaker.retry_in() == 10.0
    assert breaker.tally.trips == 1


def test_call_records_both_outcomes(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=5)
    assert breaker.call(lambda: 7) == 7
    assert breaker.tally.successes == 1

    def explode() -> None:
        raise RuntimeError("down")

    with pytest.raises(RuntimeError, match="down"):
        breaker.call(explode)
    assert breaker.tally.failures == 1
    assert breaker.consecutive_failures == 1


def test_stats_are_observable(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=1)
    breaker.allow()
    breaker.record_success()
    breaker.record_failure(RuntimeError("503"))
    breaker.allow()
    stats = breaker.stats()
    assert stats["requests"] == 2
    assert stats["allowed"] == 1
    assert stats["denied"] == 1
    assert stats["successes"] == 1
    assert stats["consecutive_failures"] == 1


def test_reset_closes_without_erasing_history(make_breaker) -> None:
    breaker = make_breaker(failure_threshold=1)
    breaker.record_failure(RuntimeError("503"))
    breaker.reset()
    assert breaker.state is model_mod.State.CLOSED
    assert breaker.tally.failures == 1


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"failure_threshold": 0}, "failure_threshold"),
        ({"cooldown_s": -1.0}, "cooldown_s"),
        ({"half_open_successes": 0}, "half_open_successes"),
    ],
)
def test_bad_configuration_is_refused(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        subject.Breaker(**kwargs)


def test_the_fake_clock_refuses_to_go_backwards() -> None:
    clock = clock_mod.FakeClock(start=5.0)
    assert clock.now() == 5.0
    clock.advance(2)
    assert clock.now() == 7.0
    with pytest.raises(ValueError, match="backwards"):
        clock.advance(-1)
