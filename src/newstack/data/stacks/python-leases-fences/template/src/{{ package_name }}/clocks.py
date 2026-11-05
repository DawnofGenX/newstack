"""Time, made explicit so a lease can be tested without sleeping."""

from __future__ import annotations


class ClockError(ValueError):
    """A clock that cannot answer."""


class ManualClock:
    """A clock that only moves when you move it.

    Every lease bug worth writing down involves a pause: a GC stop, a suspended VM, a
    signal the process never handled. A real clock makes those bugs a matter of luck to
    reproduce; this one makes them a matter of arithmetic.
    """

    def __init__(self, now_ms: int = 0) -> None:
        if now_ms < 0:
            raise ClockError(f"a clock cannot start before 0, got {now_ms}")
        self._now = now_ms

    def now_ms(self) -> int:
        return self._now

    def advance(self, ms: int) -> int:
        if ms < 0:
            raise ClockError(f"time does not run backwards, asked for {ms}")
        self._now += ms
        return self._now
