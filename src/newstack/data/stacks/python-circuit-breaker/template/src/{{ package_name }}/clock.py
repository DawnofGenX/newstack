"""Time is a dependency, so the breaker never reads the clock itself.

A breaker is mostly a rule about *when* to try again, and a test that has to sleep for a
30 second cooldown is a test nobody runs. Everything below hands the breaker a callable
that returns seconds; production gets `Monotonic`, tests get `FakeClock`.
"""

from __future__ import annotations

import time
from typing import Protocol


class Clock(Protocol):
    """The only thing the breaker needs from the outside world."""

    def now(self) -> float:
        """Return seconds from an arbitrary, non-decreasing origin."""


class Monotonic:
    """The default clock: `time.monotonic`, which a wall-clock correction cannot move."""

    def now(self) -> float:
        return time.monotonic()


class FakeClock:
    """A clock a caller can move, so a cooldown costs nothing but a line of code."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = float(start)

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("time does not run backwards")
        self._now += seconds
