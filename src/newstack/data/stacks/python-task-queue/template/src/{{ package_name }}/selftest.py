"""Offline checks for the queue's promises, on a clock we control.

Every duration is fake except in the two checks where real elapsed time is the
point (a handler outliving its lease), so the whole thing runs in about a second.
"""

from __future__ import annotations

import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import worker as worker_mod
from .store import DEAD, DONE, LEASED, READY, Job, QueueError, Store


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        suffix = f" ({detail})" if detail else ""
        print(f"FAIL {name}{suffix}")

    def equal(self, name: str, want: Any, got: Any) -> None:
        self.ok(name, want == got, f"want {want!r}, got {got!r}")

    def raises(self, name: str, fragment: str, call: Callable[[], Any]) -> None:
        try:
            call()
        except (QueueError, ValueError) as error:
            self.ok(name, fragment in str(error), f"{fragment!r} not in {str(error)!r}")
            return
        except Exception as error:  # a wrong exception is a failure too
            self.ok(name, False, f"raised {type(error).__name__}: {error}")
            return
        self.ok(name, False, "nothing was raised")


class Clock:
    """A controllable stand-in for time.time()."""

    def __init__(self, now: float = 1_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _store(directory: Path, clock: Clock, name: str = "queue.db") -> Store:
    return Store(directory / name, clock=clock, backoff_base_s=1.0, backoff_cap_s=8.0)


def _store_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    store = _store(directory, clock)

    job_id = store.push({"task": "resize", "n": 3, "text": "héllo"})
    checks.equal("push returns a uuid4 hex id", 32, len(job_id))
    checks.equal("a new job is ready", READY, store.get(job_id)["state"])
    empty = _store(directory, clock, "empty.db")
    checks.equal("nothing to claim on an empty queue", None, empty.claim("w"))
    empty.close()

    checks.raises("a non-object payload is refused", "must be an object", lambda: store.push(["x"]))
    checks.raises(
        "a payload must be JSON", "not JSON-serialisable", lambda: store.push({"o": object()})
    )
    checks.raises(
        "max_attempts 0 is refused", "at least 1", lambda: store.push({"a": 1}, max_attempts=0)
    )
    checks.raises(
        "a negative delay is refused",
        "cannot be negative",
        lambda: store.push({"a": 1}, delay_s=-1),
    )
    checks.raises(
        "a zero lease is refused", "must be positive", lambda: store.claim("w", lease_s=0)
    )

    delayed = store.push({"task": "later"}, delay_s=60.0)
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    checks.ok("the delayed job is not handed out", job is not None and job.id == job_id)
    checks.equal("the claim counts one attempt", 1, job.attempts)
    checks.equal("the payload survives the round trip", "héllo", job.payload["text"])
    checks.equal("the delayed job stays ready", READY, store.get(delayed)["state"])

    rival = _store(directory, clock)  # a second connection to the SAME database
    checks.equal("another worker cannot claim a live lease", None, rival.claim("w2"))
    checks.raises(
        "another worker cannot complete it",
        "already expired",
        lambda: rival.complete(job, "w2"),
    )

    store.complete(job, "w1", {"bytes": 42})
    checks.equal("complete moves it to done", DONE, store.get(job_id)["state"])
    checks.equal("the result is stored", {"result": {"bytes": 42}}, store.get(job_id)["result"])
    checks.raises(
        "completing twice is a lost lease", "already expired", lambda: store.complete(job, "w1")
    )

    # A lease that expires while its worker still holds it.
    second = store.push({"task": "slow"})
    claimed = store.claim("w1", lease_s=5.0)
    assert claimed is not None
    clock.advance(6.0)
    stolen = rival.claim("w2", lease_s=5.0)
    assert stolen is not None
    checks.ok("an expired lease is claimable again", stolen is not None and stolen.id == second)
    checks.equal("the retry is the second attempt", 2, stolen.attempts)
    checks.raises(
        "the original worker learns it lost the lease",
        "already expired",
        lambda: store.complete(claimed, "w1"),
    )

    # Retries and the dead-letter state.
    retried = store.push({"task": "flaky"}, max_attempts=2)
    attempt = store.claim("w1", lease_s=5.0)
    assert attempt is not None
    checks.equal("the first failure returns it to ready", READY, store.fail(attempt, "w1", "boom"))
    checks.equal(
        "the retry waits the base backoff", clock.now + 1.0, store.get(retried)["available_at"]
    )
    checks.equal("so it is not claimable yet", None, store.claim("w1"))
    clock.advance(1.0)
    attempt = store.claim("w1", lease_s=5.0)
    assert attempt is not None
    checks.equal(
        "the second failure is the last one", DEAD, store.fail(attempt, "w1", "boom again")
    )
    checks.equal("a dead job is not claimable", None, store.claim("w1"))
    checks.equal("the error is kept", "boom again", store.get(retried)["last_error"])

    checks.equal("backoff doubles", 4.0, store.backoff_for(3))
    checks.equal("backoff is capped", 8.0, store.backoff_for(9))

    counts = store.stats()
    checks.equal("done jobs are counted", 1, counts[DONE])
    checks.equal("dead jobs are counted", 1, counts[DEAD])
    checks.equal("every state is present", {READY, LEASED, DONE, DEAD}, set(counts))
    checks.equal("list filters by state", [retried], [row["id"] for row in store.list(state=DEAD)])
    checks.raises(
        "list refuses an unknown state", "unknown state", lambda: store.list(state="sold")
    )
    store.close()
    rival.close()


def _reap_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    store = _store(directory, clock, "reap.db")
    store.push({"task": "one"}, max_attempts=1)
    job = store.claim("w1", lease_s=1.0)
    checks.ok(
        "the last attempt is leased", job is not None and store.get(job.id)["state"] == LEASED
    )
    clock.advance(2.0)
    checks.equal("reap buries it", 1, store.reap())
    checks.equal("and it is dead", DEAD, store.get(job.id)["state"])
    checks.equal("reap is idempotent", 0, store.reap())
    store.close()


def _concurrency_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    path = directory / "race.db"
    setup = Store(path, clock=clock)
    expected = {setup.push({"n": n}) for n in range(40)}
    setup.close()

    claimed: list[str] = []
    lock = threading.Lock()
    errors: list[str] = []

    def work() -> None:
        try:
            store = Store(path, clock=clock)
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
        except Exception as error:  # surfaced below instead of killing the thread silently
            errors.append(f"{type(error).__name__}: {error}")

    threads = [threading.Thread(target=work) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    checks.equal("no worker raised", [], errors)
    checks.equal("every job was claimed once", 40, len(claimed))
    checks.equal("no job was handed out twice", 40, len(set(claimed)))
    checks.equal("and they are the jobs that were pushed", expected, set(claimed))

    store = Store(path, clock=clock)
    checks.equal("all of them finished", 40, store.stats()[DONE])
    checks.equal("each took one attempt", {1}, {row["attempts"] for row in store.list()})
    store.close()


def _worker_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    store = _store(directory, clock, "worker.db")

    store.push({"task": "add"})
    job = store.claim("w1", lease_s=5.0)
    assert job is not None  # the queue is not empty here
    checks.equal(
        "a good handler completes the job",
        DONE,
        worker_mod.process(store, job, lambda j: {"sum": 2}, worker="w1"),
    )

    store.push({"task": "explode"}, max_attempts=2)
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    checks.equal(
        "a raising handler leaves it retryable",
        READY,
        worker_mod.process(store, job, _boom, worker="w1"),
    )
    checks.ok("and the error is kept", "ValueError: nope" in store.get(job.id)["last_error"])

    store.push({"task": "explode"}, max_attempts=1)
    job = store.claim("w1", lease_s=5.0)
    assert job is not None
    checks.equal(
        "the last attempt buries it", DEAD, worker_mod.process(store, job, _boom, worker="w1")
    )

    checks.raises(
        "a heartbeat longer than the lease is refused",
        "well below lease_s",
        lambda: worker_mod.process(
            store,
            Job("x", "default", {}, 1, 1),
            lambda j: None,
            worker="w1",
            lease_s=1.0,
            heartbeat_s=1.0,
        ),
    )

    clock.advance(10.0)  # past every backoff still pending in this file
    alive = _store(directory, clock, "alive.db")
    alive.push({"task": "slow"})
    job = alive.claim("w1", lease_s=1.0)
    assert job is not None
    checks.equal(
        "a heartbeat keeps a slow job alive",
        DONE,
        worker_mod.process(alive, job, _slow_handler, worker="w1", lease_s=1.0, heartbeat_s=0.05),
    )
    checks.equal("and it only ran once", 1, alive.get(job.id)["attempts"])

    # This one needs the real clock: a fake clock does not move while we sleep.
    stolen_store = Store(directory / "stolen.db", clock=time.time)
    stolen_store.push({"task": "slow"})
    job = stolen_store.claim("w1", lease_s=0.2)
    assert job is not None
    time.sleep(0.3)
    checks.ok("without a heartbeat the job is stolen", _claim_id(stolen_store) == job.id)
    stolen_store.close()
    alive.close()
    store.close()


def _slow_handler(job: Job) -> dict[str, bool]:
    time.sleep(0.3)
    return {"slow": True}


def _boom(job: Job) -> None:
    raise ValueError("nope")


def _claim_id(store: Store) -> str | None:
    job = store.claim("rival", lease_s=5.0)
    return None if job is None else job.id


def _drain_checks(checks: Checks, directory: Path) -> None:
    clock = Clock()
    store = _store(directory, clock, "drain.db")
    for n in range(3):
        store.push({"n": n})
    report = worker_mod.drain(store, lambda j: j.payload["n"], worker="drainer")
    checks.equal("drain processes everything", 3, report.processed)
    checks.equal("drain counts the claims", 3, report.claimed)
    checks.equal(
        "drain on an empty queue does nothing",
        0,
        worker_mod.drain(store, lambda j: 1, worker="d").claimed,
    )

    store.push({"n": 9}, max_attempts=1)
    report = worker_mod.drain(store, _boom, worker="d")
    checks.equal("drain counts a dead letter separately", 1, report.dead)
    checks.equal("drain counts no success for it", 0, report.processed)

    for n in range(3):
        store.push({"n": n})
    checks.equal(
        "max_jobs stops the loop",
        1,
        worker_mod.drain(store, lambda j: 1, worker="d", max_jobs=1).processed,
    )
    checks.equal("and the rest stay ready", 2, store.stats()[READY])
    store.close()


def main() -> int:
    checks = Checks()
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        _store_checks(checks, directory)
        _reap_checks(checks, directory)
        _concurrency_checks(checks, directory)
        _worker_checks(checks, directory)
        _drain_checks(checks, directory)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
