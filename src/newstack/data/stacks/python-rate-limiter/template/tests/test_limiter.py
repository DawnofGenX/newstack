"""The keyed limiter: independence between keys, pruning, and the thread proof."""

from __future__ import annotations

import threading

import pytest

from {{ package_name }} import clock as clock_mod
from {{ package_name }} import limiter as subject
from {{ package_name }} import model as model_mod


def limiter(limit=2, per_seconds=1, capacity=None, max_keys=None):
    fake = clock_mod.FakeClock()
    return subject.Limiter(
        model_mod.Config(limit=limit, per_seconds=per_seconds, capacity=capacity),
        fake,
        max_keys=max_keys,
    ), fake


def test_keys_have_independent_buckets() -> None:
    bucket, _ = limiter()
    assert bucket.check("a").allowed
    assert bucket.check("a").allowed
    assert not bucket.check("a").allowed
    assert bucket.check("b").allowed


def test_pruning_drops_only_the_keys_that_refilled() -> None:
    bucket, fake = limiter()
    bucket.check("old")
    for _ in range(2):
        bucket.check("old")
    fake.advance_s(5)
    bucket.check("fresh")
    assert bucket.prune() == 1
    assert len(bucket) == 1


def test_max_keys_bounds_the_table() -> None:
    bucket, _ = limiter(max_keys=5)
    for index in range(50):
        bucket.check(f"user-{index}")
    assert len(bucket) == 5
    assert bucket.stats()["evicted"] >= 45


def test_waiting_does_not_spend() -> None:
    bucket, fake = limiter(limit=1, per_seconds=10)
    assert bucket.wait_time_us("k") == 0
    bucket.check("k")
    assert bucket.wait_time_us("k") == 10_000_000
    assert bucket.stats()["checks"] == 1
    fake.advance_s(10)
    assert bucket.check("k").allowed


def test_an_empty_key_is_refused() -> None:
    bucket, _ = limiter()
    with pytest.raises(ValueError, match="non-empty"):
        bucket.check("")


def test_threads_cannot_spend_a_bucket_twice() -> None:
    bucket, _ = limiter(limit=20, per_seconds=1)
    allowed = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(100):
            if bucket.check("shared").allowed:
                with lock:
                    allowed.append(1)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(allowed) == 20


def test_the_rate_holds_over_a_long_run() -> None:
    bucket, fake = limiter(limit=5, per_seconds=1, capacity=5)
    allowed = 0
    for _ in range(600):
        fake.advance(10_000)
        allowed += 1 if bucket.check("k").allowed else 0
    # 6 seconds of traffic at 5/s, plus the burst, minus the first interval.
    assert 25 <= allowed <= 35
