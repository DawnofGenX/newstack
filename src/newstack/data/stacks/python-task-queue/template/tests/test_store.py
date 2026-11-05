"""The store's guarantees: one claim per job, leases that expire, retries, dead ends."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

import pytest

from {{ package_name }} import store as subject

Store = subject.Store


def test_push_returns_an_id_and_a_ready_row(store: Store) -> None:
    job_id = store.push({"task": "resize"})
    row = store.get(job_id)
    assert len(job_id) == 32
    assert row["state"] == subject.READY
    assert row["attempts"] == 0
    assert store.stats()[subject.READY] == 1


def test_a_payload_must_be_an_object(store: Store) -> None:
    with pytest.raises(subject.QueueError, match="must be an object"):
        store.push(["nope"])


def test_a_payload_must_be_json(store: Store) -> None:
    with pytest.raises(subject.QueueError, match="not JSON-serialisable"):
        store.push({"when": object()})


def test_claim_counts_the_attempt_and_leases_it(store: Store) -> None:
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    assert job.id == job_id
    assert job.attempts == 1
    assert store.get(job_id)["state"] == subject.LEASED
    assert store.claim("w2", lease_s=5.0) is None


def test_a_delayed_job_waits(store: Store, clock: Callable[[], float]) -> None:
    job_id = store.push({"n": 1}, delay_s=30.0)
    assert store.claim("w1", lease_s=5.0) is None
    clock.advance(31.0)  # type: ignore[attr-defined]
    job = store.claim("w1", lease_s=5.0)
    assert job is not None and job.id == job_id


def test_an_expired_lease_can_be_reclaimed(
    store: Store, clock: Callable[[], float], make_store: Callable[..., Store]
) -> None:
    job_id = store.push({"n": 1})
    first = store.claim("w1", lease_s=5.0)
    clock.advance(6.0)  # type: ignore[attr-defined]
    second = make_store().claim("w2", lease_s=5.0)
    assert second is not None
    assert second.id == job_id
    assert second.attempts == 2
    with pytest.raises(subject.LeaseLost, match="already expired"):
        store.complete(first, "w1")  # type: ignore[arg-type]


def test_a_heartbeat_keeps_the_lease(
    store: Store, clock: Callable[[], float], make_store: Callable[..., Store]
) -> None:
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    clock.advance(4.0)  # type: ignore[attr-defined]
    store.heartbeat(job, "w1", lease_s=5.0)
    clock.advance(4.0)  # type: ignore[attr-defined]
    assert make_store().claim("w2", lease_s=5.0) is None
    store.complete(job, "w1")
    assert store.get(job_id)["state"] == subject.DONE


def test_a_failure_returns_the_job_with_backoff(store: Store, clock: Callable[[], float]) -> None:
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    state = store.fail(job, "w1", "ValueError: nope")
    assert state == subject.READY
    row = store.get(job_id)
    assert row["available_at"] == pytest.approx(clock() + 1.0)  # type: ignore[operator]
    assert row["last_error"] == "ValueError: nope"
    assert store.claim("w1", lease_s=5.0) is None


def test_backoff_grows_and_is_capped(store: Store) -> None:
    assert [store.backoff_for(n) for n in (1, 2, 3, 4)] == [1.0, 2.0, 4.0, 8.0]
    assert store.backoff_for(30) == 8.0


def test_a_retry_waits_for_its_backoff(store: Store, clock: Callable[[], float]) -> None:
    job_id = store.push({"n": 1}, max_attempts=2)
    store.fail(store.claim("w1", lease_s=5.0), "w1", "one")  # type: ignore[arg-type]
    assert store.claim("w1", lease_s=5.0) is None, "the retry must wait out the backoff"
    clock.advance(1.0)  # type: ignore[attr-defined]
    second = store.claim("w1", lease_s=5.0)
    assert second is not None and second.id == job_id
    assert store.fail(second, "w1", "two") == subject.DEAD
    assert store.get(job_id)["state"] == subject.DEAD
    assert store.claim("w1", lease_s=5.0) is None


def test_a_dead_lease_is_reaped_when_its_attempts_run_out(
    store: Store, clock: Callable[[], float]
) -> None:
    job_id = store.push({"n": 1}, max_attempts=1)
    store.claim("w1", lease_s=1.0)
    clock.advance(2.0)  # type: ignore[attr-defined]
    assert store.reap() == 1
    assert store.get(job_id)["state"] == subject.DEAD
    assert store.reap() == 0


def test_complete_stores_the_result(store: Store) -> None:
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=5.0)
    store.complete(job, "w1", {"ok": True})  # type: ignore[arg-type]
    assert store.get(job_id)["result"] == {"result": {"ok": True}}
    with pytest.raises(subject.LeaseLost):
        store.complete(job, "w1")  # type: ignore[arg-type]


def test_list_and_stats(store: Store) -> None:
    first = store.push({"n": 1})
    second = store.push({"n": 2}, queue="mail")
    claimed = store.claim("w1", lease_s=5.0)
    assert claimed is not None
    ready = [row["id"] for row in store.list(state=subject.READY)]
    assert ready == [job_id for job_id in (first, second) if job_id != claimed.id]
    assert [row["id"] for row in store.list(state=subject.LEASED)] == [claimed.id]
    assert [row["queue"] for row in store.list(queue="mail")] == ["mail"]
    counts = store.stats()
    assert counts[subject.LEASED] == 1 and counts[subject.READY] == 1
    with pytest.raises(subject.QueueError, match="unknown state"):
        store.list(state="sold")


def test_only_one_thread_can_claim_a_job(tmp_path: Path, clock: Callable[[], float]) -> None:
    """Four connections, forty jobs: every job is handed out exactly once."""
    path = tmp_path / "race.db"
    setup = subject.Store(path, clock=clock)
    expected = {setup.push({"n": n}) for n in range(40)}
    setup.close()

    claimed: list[str] = []
    lock = threading.Lock()

    def work() -> None:
        # A connection belongs to the thread that opened it, so each worker
        # opens — and closes — its own.
        store = subject.Store(path, clock=clock)
        try:
            while True:
                job = store.claim("racer", lease_s=30.0)
                if job is None:
                    return
                with lock:
                    claimed.append(job.id)
                store.complete(job, "racer")
        finally:
            store.close()

    threads = [threading.Thread(target=work) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(claimed) == 40
    assert len(set(claimed)) == 40
    assert set(claimed) == expected

    check = subject.Store(path, clock=clock)
    try:
        assert check.stats()[subject.DONE] == 40
        assert {row["attempts"] for row in check.list()} == {1}
    finally:
        check.close()


def test_the_lease_must_be_positive(store: Store) -> None:
    store.push({"n": 1})
    with pytest.raises(subject.QueueError, match="must be positive"):
        store.claim("w1", lease_s=0)
