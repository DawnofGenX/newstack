"""Clocks are injected, so a limiter that refills once a second can be tested in microseconds."""

from __future__ import annotations

import time
from typing import Protocol


class Clock(Protocol):
    """The one thing the limiter needs from the world: what time is it, in microseconds."""

    def now_us(self) -> int: ...


class Monotonic:
    """Real time, in whole microseconds, from a clock that cannot go backwards."""

    def now_us(self) -> int:
        return time.monotonic_ns() // 1000


class FakeClock:
    """A clock you can move by hand; the limiter never calls `time` itself."""

    def __init__(self, start_us: int = 0) -> None:
        self._now = start_us

    def now_us(self) -> int:
        return self._now

    def advance(self, microseconds: int) -> None:
        if microseconds < 0:
            raise ValueError("time does not run backwards")
        self._now += microseconds

    def advance_s(self, seconds: float) -> None:
        self.advance(round(seconds * 1_000_000))
