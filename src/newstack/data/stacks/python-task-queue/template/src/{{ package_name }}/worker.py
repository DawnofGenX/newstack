"""Running a claimed job without letting the lease expire underneath it.

A handler that runs longer than the lease is the ordinary case, not the exotic one
— a retry with backoff, a slow API call, a batch. Without a heartbeat another
worker legitimately takes the job over and both of you now believe the job is
yours. The heartbeat is therefore not an optimisation: it is what makes a lease
longer than a request.

The heartbeat needs a second connection, and it must be opened *inside* the heartbeat
thread: a SQLite connection may only be used by the thread that created it, so opening
one in the caller and using it from here raises ProgrammingError however separate the
files are.
"""

from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .store import DEAD, DEFAULT_LEASE_S, DONE, Job, LeaseLost, Store

Handler = Callable[[Job], Any]


@dataclass(frozen=True)
class Report:
    processed: int = 0
    failed: int = 0
    dead: int = 0
    lost: int = 0

    @property
    def claimed(self) -> int:
        return self.processed + self.failed + self.dead + self.lost

    def as_dict(self) -> dict[str, int]:
        return {
            "claimed": self.claimed,
            "processed": self.processed,
            "failed": self.failed,
            "dead": self.dead,
            "lost": self.lost,
        }


def _beat(
    factory: Callable[[], Store],
    job: Job,
    worker: str,
    lease_s: float,
    every_s: float,
    stop: threading.Event,
) -> None:
    """Renew the lease on a connection this thread owns, until the job is over."""
    store = factory()
    try:
        while not stop.wait(every_s):
            try:
                store.heartbeat(job, worker, lease_s=lease_s)
            except LeaseLost:
                return
    finally:
        store.close()


def process(
    store: Store,
    job: Job,
    handler: Handler,
    *,
    worker: str,
    lease_s: float = DEFAULT_LEASE_S,
    heartbeat_s: float | None = None,
    store_factory: Callable[..., Store] = Store,
) -> str:
    """Run one job and finish it honestly. Returns the job's new state."""
    if heartbeat_s is not None and heartbeat_s >= lease_s:
        raise ValueError("heartbeat_s must be well below lease_s, or the lease expires first")
    beater: threading.Thread | None = None
    stop = threading.Event()
    if heartbeat_s is not None:
        factory = functools.partial(store_factory, store.path, clock=store.clock)
        beater = threading.Thread(
            target=_beat,
            args=(factory, job, worker, lease_s, heartbeat_s, stop),
            name=f"heartbeat-{job.id}",
            daemon=True,
        )
        beater.start()
    try:
        result = handler(job)
    except Exception as error:  # a failing handler is a failed attempt, not a crash
        state = store.fail(job, worker, f"{type(error).__name__}: {error}")
        return state
    finally:
        stop.set()
        if beater is not None:
            beater.join(timeout=5.0)
    store.complete(job, worker, result)
    return DONE


def drain(
    store: Store,
    handler: Handler,
    *,
    worker: str,
    max_jobs: int | None = None,
    lease_s: float = DEFAULT_LEASE_S,
    heartbeat_s: float | None = None,
    idle_sleep_s: float = 0.0,
    polls: int = 1,
    sleep: Callable[[float], None] = time.sleep,
) -> Report:
    """Process until nothing is claimable (or ``max_jobs`` is reached).

    ``polls`` is how many empty claims in a row mean "there is nothing left": one
    is right for a batch run, more is right when another producer is still writing.
    """
    processed = failed = dead = lost = 0
    empty = 0
    while max_jobs is None or processed + failed + dead + lost < max_jobs:
        job = store.claim(worker, lease_s=lease_s)
        if job is None:
            empty += 1
            if empty >= max(1, polls):
                break
            sleep(idle_sleep_s)
            continue
        empty = 0
        try:
            state = process(
                store,
                job,
                handler,
                worker=worker,
                lease_s=lease_s,
                heartbeat_s=heartbeat_s,
            )
        except LeaseLost:
            lost += 1
            continue
        if state == DONE:
            processed += 1
        elif state == DEAD:
            dead += 1
        else:
            failed += 1
    return Report(processed=processed, failed=failed, dead=dead, lost=lost)
