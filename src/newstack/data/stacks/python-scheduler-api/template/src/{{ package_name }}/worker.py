"""The ticker: one thread, a monotonic loop, and a stop that actually stops."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from . import db, jobs


class Scheduler:
    """Claims due jobs on a fixed interval and records what happened.

    The loop is deliberately dumb: sleep, claim, run, record, repeat. Everything
    that survives a restart lives in the database, so the thread holds no state
    worth losing — which is what makes `stop()` safe to call from a signal
    handler.
    """

    def __init__(
        self,
        path: Path | str,
        *,
        tick: float = 0.1,
        batch: int = 8,
        clock: callable = time.time,
    ) -> None:
        self.path = path
        self.tick = tick
        self.batch = batch
        self.clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: sqlite3.Connection | None = None
        self._last_error: str | None = None
        self.ticks = 0
        self.ran = 0

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._connection = db.connect(self.path)
        db.migrate(self._connection)
        self._thread = threading.Thread(target=self._loop, name="scheduler", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001 - a broken tick must not kill the loop
                self._last_error = f"{type(exc).__name__}: {exc}"
            # `wait` instead of `sleep` so stop() does not have to wait out a tick.
            self._stop.wait(self.tick)

    # -- one tick ----------------------------------------------------------
    def run_once(self) -> int:
        if self._connection is None:
            self._connection = db.connect(self.path)
            db.migrate(self._connection)
        at = self.clock()
        claimed = jobs.claim(self._connection, at=at, limit=self.batch)
        self.ticks += 1
        for job in claimed:
            jobs.execute(self._connection, job, at=at, started_at=at)
        self.ran += len(claimed)
        return len(claimed)

    def drain(self, limit: int = 100) -> int:
        """Run due jobs synchronously — for tests and for a manual kick."""
        total = 0
        for _ in range(limit):
            moved = self.run_once()
            total += moved
            if moved == 0:
                break
        return total
