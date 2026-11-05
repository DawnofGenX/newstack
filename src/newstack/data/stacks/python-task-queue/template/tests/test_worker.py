"""The worker: a lease that outlives the handler, and a job that never disappears."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest

from {{ package_name }} import store as store_module
from {{ package_name }} import worker as subject

Store = store_module.Store


def test_a_good_handler_completes_the_job(store: Store) -> None:
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    assert (
        subject.process(store, job, lambda j: {"n": j.payload["n"]}, worker="w1")
        == store_module.DONE
    )
    assert store.get(job_id)["result"] == {"result": {"n": 1}}


def test_a_raising_handler_returns_the_job(store: Store) -> None:
    job_id = store.push({"n": 1}, max_attempts=2)
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    assert subject.process(store, job, boom, worker="w1") == store_module.READY
    assert "ValueError: nope" in store.get(job_id)["last_error"]


def test_the_last_attempt_is_dead_lettered(store: Store) -> None:
    job_id = store.push({"n": 1}, max_attempts=1)
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    assert subject.process(store, job, boom, worker="w1") == store_module.DEAD
    assert store.get(job_id)["state"] == store_module.DEAD


def test_a_heartbeat_must_be_well_below_the_lease(store: Store) -> None:
    store.push({"n": 1})
    job = store.claim("w1", lease_s=1.0)
    assert job is not None
    with pytest.raises(ValueError, match="well below lease_s"):
        subject.process(store, job, lambda j: None, worker="w1", lease_s=1.0, heartbeat_s=1.0)


def test_a_slow_handler_survives_on_its_heartbeat(make_real_store: Callable[..., Store]) -> None:
    store = make_real_store()
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=0.4)
    assert job is not None
    rival = make_real_store()
    state = subject.process(
        store,
        job,
        lambda j: time.sleep(0.5) or {"slow": True},
        worker="w1",
        lease_s=0.4,
        heartbeat_s=0.05,
    )
    assert state == store_module.DONE
    assert rival.claim("w2", lease_s=5.0) is None, "the lease was renewed while the handler ran"
    assert store.get(job_id)["attempts"] == 1


def test_without_heartbeat_the_job_is_stolen(make_real_store: Callable[..., Store]) -> None:
    store = make_real_store()
    job_id = store.push({"n": 1})
    job = store.claim("w1", lease_s=0.2)
    assert job is not None
    time.sleep(0.3)
    stolen = make_real_store().claim("w2", lease_s=5.0)
    assert stolen is not None and stolen.id == job_id
    with pytest.raises(store_module.LeaseLost):
        store.complete(job, "w1")


def test_drain_works_until_the_queue_is_empty(store: Store) -> None:
    for n in range(3):
        store.push({"n": n})
    report = subject.drain(store, lambda j: j.payload["n"], worker="drainer")
    assert report.processed == 3
    assert report.claimed == 3
    assert report.as_dict() == {
        "claimed": 3,
        "processed": 3,
        "failed": 0,
        "dead": 0,
        "lost": 0,
    }
    assert subject.drain(store, lambda j: 1, worker="drainer").claimed == 0


def test_drain_honours_max_jobs(store: Store) -> None:
    for n in range(3):
        store.push({"n": n})
    assert subject.drain(store, lambda j: 1, worker="d", max_jobs=1).processed == 1
    assert store.stats()[store_module.READY] == 2


def test_drain_counts_dead_letters_separately(store: Store) -> None:
    for n in range(2):
        store.push({"n": n}, max_attempts=1)
    report = subject.drain(store, boom, worker="d")
    assert report.dead == 2
    assert report.processed == 0


def boom(job: store_module.Job) -> Any:
    raise ValueError("nope")
