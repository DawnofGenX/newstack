"""Issuing identifiers: the clock, the sequence, and what happens when they disagree.

The sequence is a promise the clock cannot keep on its own: 12 bits allow 4096
identifiers in one millisecond, and the generator must either wait for the next
millisecond or refuse. A clock that steps backwards is the other half of the
same problem, and the two strategies here spend different budgets to survive it.
"""

from __future__ import annotations

import time

from .layout import (
    EPOCH_MS,
    IDS_PER_MS,
    MAX_SEQUENCE,
    _check_worker,
    compose,
    decode,
)


class ClockError(RuntimeError):
    """The clock cannot support the next identifier."""


class ManualClock:
    """A clock that moves when a test tells it to.

    ``wait_until`` is how a real wall clock passes time; here it jumps, and
    counts the jump, so a test can tell a wait apart from a refusal.
    """

    def __init__(self, now_ms: int) -> None:
        if isinstance(now_ms, bool) or not isinstance(now_ms, int):
            raise ClockError(f"a clock starts at a whole number of ms, not {now_ms!r}")
        self._now = now_ms
        self.waits = 0

    def now_ms(self) -> int:
        return self._now

    def set(self, now_ms: int) -> None:
        self._now = now_ms

    def advance(self, ms: int) -> None:
        if ms < 0:
            raise ClockError("advance() moves forward; use set() to step back")
        self._now += ms

    def wait_until(self, now_ms: int) -> bool:
        if now_ms <= self._now:
            return False
        self._now = now_ms
        self.waits += 1
        return True


class WallClock:
    """The real clock, with the same three methods."""

    def now_ms(self) -> int:
        return time.time_ns() // 1_000_000

    def wait_until(self, now_ms: int) -> bool:
        while True:
            remaining = now_ms - self.now_ms()
            if remaining <= 0:
                return True
            time.sleep(min(remaining, 50) / 1_000)


class SnowflakeGenerator:
    """One worker's view of the layout.

    ``on_rollback`` decides what a backwards step costs:

    * ``"refuse"`` (the default) raises, so the caller learns the clock is
      broken instead of receiving identifiers that quietly reuse a millisecond.
    * ``"hold"`` keeps issuing inside the last millisecond it saw, spending the
      sequence budget; when that budget is gone it raises as well.
    """

    def __init__(
        self,
        worker: int,
        *,
        clock=None,
        epoch_ms: int = EPOCH_MS,
        on_rollback: str = "refuse",
    ) -> None:
        self.worker = _check_worker(worker)
        if on_rollback not in {"refuse", "hold"}:
            raise ClockError(f"on_rollback is 'refuse' or 'hold', not {on_rollback!r}")
        self.clock = WallClock() if clock is None else clock
        self.epoch_ms = epoch_ms
        self.on_rollback = on_rollback
        self._last_ms: int | None = None
        self._sequence = 0
        self.issued = 0
        self.waits = 0
        self.holds = 0

    @property
    def last_ms(self) -> int | None:
        return self._last_ms

    def relative_ms(self) -> int:
        return self.clock.now_ms() - self.epoch_ms

    def next_id(self) -> int:
        now = self.relative_ms()
        if self._last_ms is not None and now < self._last_ms:
            if self.on_rollback == "refuse":
                behind = self._last_ms - now
                raise ClockError(
                    f"the clock moved back {behind} ms after identifier {self.issued}; "
                    "issuing again would reuse a millisecond, so this generator refuses"
                )
            self.holds += 1
            now = self._last_ms
        if self._last_ms is None or now > self._last_ms:
            self._last_ms = now
            self._sequence = 0
        else:
            self._sequence += 1
            if self._sequence > MAX_SEQUENCE:
                if not self.clock.wait_until(self.epoch_ms + now + 1):
                    raise ClockError(
                        f"{IDS_PER_MS} identifiers in one millisecond is the whole sequence, "
                        "and this clock cannot move forward to the next one"
                    )
                self.waits += 1
                self._last_ms = now + 1
                self._sequence = 0
        self.issued += 1
        return compose(self._last_ms, self.worker, self._sequence)

    def decode(self, value: int):
        return decode(value)

    def stats(self) -> dict[str, int]:
        return {
            "worker": self.worker,
            "issued": self.issued,
            "waits": self.waits,
            "holds": self.holds,
        }


def generate(
    count: int, *, worker: int, clock, epoch_ms: int = EPOCH_MS, on_rollback: str = "refuse"
) -> list[int]:
    """Issue ``count`` identifiers from one worker."""
    if count < 0:
        raise ClockError("a count is not negative")
    generator = SnowflakeGenerator(worker, clock=clock, epoch_ms=epoch_ms, on_rollback=on_rollback)
    return [generator.next_id() for _ in range(count)]
