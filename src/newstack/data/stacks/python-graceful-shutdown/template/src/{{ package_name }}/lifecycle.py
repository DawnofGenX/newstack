"""The state machine behind a shutdown: running, draining, stopped - entered once.

Nothing here touches sockets or signals. That separation is deliberate: the sequence a
deploy depends on can then be tested without spawning a process, and the code that does
touch signals stays small enough to read.
"""

from __future__ import annotations

import threading
import time
from enum import StrEnum


class Phase(StrEnum):
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"


class Lifecycle:
    """Counts in-flight requests and decides who may still start one."""

    def __init__(self, drain_timeout: float = 10.0) -> None:
        if drain_timeout <= 0:
            raise ValueError("drain timeout must be positive")
        self.drain_timeout = drain_timeout
        self.drain_ok = False
        self.drained_in = 0.0
        self._phase = Phase.RUNNING
        self._lock = threading.Lock()
        self._idle = threading.Condition(self._lock)
        self._in_flight = 0
        self._served = 0
        self._started_draining = 0.0

    @property
    def phase(self) -> Phase:
        with self._lock:
            return self._phase

    @property
    def in_flight(self) -> int:
        with self._lock:
            return self._in_flight

    @property
    def served(self) -> int:
        with self._lock:
            return self._served

    def begin_drain(self) -> bool:
        """Return True only for the first caller: a second signal is not a second drain."""
        with self._lock:
            if self._phase is not Phase.RUNNING:
                return False
            self._phase = Phase.DRAINING
            self._started_draining = time.monotonic()
            self._idle.notify_all()
            return True

    def admit(self) -> bool:
        """Count a request only while running.

        A connection opened before the signal can still carry a new request afterwards.
        That request is refused rather than counted: letting it in is how a drain
        finishes, the process exits, and the client sees a reset instead of a 503.
        """
        with self._lock:
            if self._phase is not Phase.RUNNING:
                return False
            self._in_flight += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._in_flight -= 1
            self._served += 1
            if self._in_flight == 0:
                self._idle.notify_all()

    def wait_for_idle(self, timeout: float | None = None) -> bool:
        """Wait for in-flight work, bounded; records the outcome on the instance."""
        budget = self.drain_timeout if timeout is None else timeout
        deadline = time.monotonic() + budget
        with self._lock:
            while self._in_flight > 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.drained_in = time.monotonic() - self._started_draining
                    return False
                self._idle.wait(remaining)
            self._phase = Phase.STOPPED
            self.drained_in = time.monotonic() - self._started_draining
            self.drain_ok = True
            return True
