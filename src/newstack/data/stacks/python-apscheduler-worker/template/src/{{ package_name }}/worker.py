"""Run a fixed number of scheduler ticks."""

from __future__ import annotations

import threading

from apscheduler.schedulers.background import BackgroundScheduler

from .db import count_runs, record_tick, reset_db


def run_ticks(count: int) -> int:
    reset_db()
    state = {"done": 0}
    event = threading.Event()

    def job() -> None:
        state["done"] += 1
        record_tick(state["done"])
        if state["done"] >= count:
            event.set()

    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", seconds=0.1, max_instances=1)
    scheduler.start()
    finished = event.wait(timeout=max(1.0, count * 2.0 + 5.0))
    scheduler.shutdown(wait=True)
    if not finished:
        raise RuntimeError("timed out waiting for ticks")
    return count_runs()