from __future__ import annotations

import threading
import time

import pytest
from support import Clock

from {{ package_name }} import cache as subject
from {{ package_name }} import model


def test_a_miss_loads_and_a_second_call_is_a_hit() -> None:
    calls: list[str] = []

    def loader(key: str) -> str:
        calls.append(key)
        return key.upper()

    cache = subject.SingleFlight(loader)
    first = cache.get("a")
    second = cache.get("a")
    assert first.hit is False and first.waited is False
    assert second.hit is True and second.value == "A"
    assert calls == ["a"]
    assert cache.stats.as_dict() == {"calls": 2, "hits": 1, "waits": 0, "loads": 1, "failures": 0}


def test_an_empty_or_non_string_key_is_refused() -> None:
    cache = subject.SingleFlight(lambda key: key)
    with pytest.raises(model.LoadError, match="key must not be empty"):
        cache.get("  ")
    with pytest.raises(model.LoadError, match="key must be a string"):
        cache.get(3)  # type: ignore[arg-type]


def test_a_bad_ttl_is_refused_at_construction() -> None:
    with pytest.raises(model.LoadError, match="ttl must be positive"):
        subject.SingleFlight(lambda key: key, ttl_s=0)
    with pytest.raises(model.LoadError, match="ttl must be a number"):
        subject.SingleFlight(lambda key: key, ttl_s=True)  # type: ignore[arg-type]


def test_twenty_threads_share_one_load() -> None:
    calls = {"n": 0}

    def loader(key: str) -> str:
        calls["n"] += 1
        time.sleep(0.05)
        return f"{key}-value"

    cache = subject.SingleFlight(loader)
    values: list[object] = []
    gate = threading.Barrier(21)
    lock = threading.Lock()

    def worker() -> None:
        gate.wait()
        answer = cache.get("k")
        with lock:
            values.append(answer.value)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for thread in threads:
        thread.start()
    gate.wait()
    for thread in threads:
        thread.join()

    assert calls["n"] == 1
    assert cache.stats.waits == 19
    assert set(values) == {"k-value"}


def test_a_slow_key_does_not_hold_up_a_fast_one() -> None:
    cache = subject.SingleFlight(lambda key: time.sleep(0.3) if key == "slow" else "fast")
    thread = threading.Thread(target=lambda: cache.get("slow"))
    thread.start()
    time.sleep(0.05)
    started = time.perf_counter()
    answer = cache.get("fast")
    elapsed = time.perf_counter() - started
    thread.join()
    assert answer.value == "fast"
    assert elapsed < 0.15


def test_a_failure_reaches_every_waiter_and_is_not_cached() -> None:
    attempts = {"n": 0}

    def loader(_key: str) -> str:
        attempts["n"] += 1
        time.sleep(0.02)
        if attempts["n"] == 1:
            raise ConnectionError("down")
        return "recovered"

    cache = subject.SingleFlight(loader)
    errors: list[BaseException] = []
    gate = threading.Barrier(5)
    lock = threading.Lock()

    def worker() -> None:
        gate.wait()
        try:
            cache.get("k")
        except BaseException as error:
            with lock:
                errors.append(error)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    gate.wait()
    for thread in threads:
        thread.join()

    assert len(errors) == 4
    assert all(isinstance(error, model.FlightError) for error in errors)
    assert cache.stats.loads == 1
    assert cache.get("k").value == "recovered"
    assert cache.stats.loads == 2


def test_the_leader_wraps_the_original_error_too() -> None:
    cache = subject.SingleFlight(lambda key: (_ for _ in ()).throw(KeyError("nope")))
    with pytest.raises(model.FlightError) as caught:
        cache.get("k")
    assert isinstance(caught.value.error, KeyError)
    assert len(cache) == 0


def test_a_ttl_starts_when_the_value_became_readable() -> None:
    clock = Clock()
    cache = subject.SingleFlight(lambda key: f"{key}-{clock.now():.1f}", ttl_s=1.0, clock=clock.now)
    first = cache.get("k")
    clock.advance(0.99)
    assert cache.get("k").hit is True
    clock.advance(0.02)
    after = cache.get("k")
    assert after.hit is False
    assert after.value != first.value


def test_peek_never_loads_and_forget_drops() -> None:
    cache = subject.SingleFlight(lambda key: key.upper())
    assert cache.peek("k") is None
    cache.get("k")
    assert cache.peek("k").value == "K"  # type: ignore[union-attr]
    assert cache.forget("k") is True
    assert cache.forget("k") is False
    assert len(cache) == 0
