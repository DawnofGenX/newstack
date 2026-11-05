"""The clock: wall time, a counter, and the rule that keeps it monotone."""

from __future__ import annotations

from collections.abc import Callable

from .stamp import Stamp


class ClockError(ValueError):
    """A clock that cannot be trusted to answer, rather than one that guesses."""


class ManualWall:
    """A wall clock a test can move, including backwards.

    Real clocks do go backwards: NTP steps, virtual machines resume from a
    snapshot, and a laptop wakes from sleep with a stale timer.
    """

    def __init__(self, now_ms: int = 1_700_000_000_000) -> None:
        if isinstance(now_ms, bool) or not isinstance(now_ms, int):
            raise ClockError(f"a wall clock holds whole milliseconds, not {now_ms!r}")
        self._now_ms = now_ms

    def now(self) -> int:
        return self._now_ms

    def set(self, now_ms: int) -> None:
        if isinstance(now_ms, bool) or not isinstance(now_ms, int):
            raise ClockError(f"a wall clock holds whole milliseconds, not {now_ms!r}")
        self._now_ms = now_ms

    def advance(self, ms: int) -> int:
        if isinstance(ms, bool) or not isinstance(ms, int):
            raise ClockError(f"advance takes whole milliseconds, not {ms!r}")
        if ms < 0:
            raise ClockError(f"advance cannot go backwards, not {ms}; use set() to step back")
        self._now_ms += ms
        return self._now_ms


class HybridClock:
    """A physical clock with a logical counter, as in Kulkarni et al. 2014.

    Two invariants, and both are testable:

    * every stamp this clock hands out is strictly greater than the last one,
      whatever the wall clock does;
    * receiving a stamp that is ahead of us moves us past it, so a message
      cannot arrive in the past.
    """

    def __init__(
        self,
        node: str,
        *,
        wall_ms: Callable[[], int],
        max_skew_ms: int | None = None,
    ) -> None:
        if not node:
            raise ClockError("a clock needs a node name, so ties can be broken")
        if max_skew_ms is not None and max_skew_ms < 0:
            raise ClockError(f"max_skew_ms cannot be negative, not {max_skew_ms}")
        self.node = node
        self._wall_ms = wall_ms
        self.max_skew_ms = max_skew_ms
        self._physical_ms = 0
        self._logical = 0
        self.events = 0
        self.receives = 0
        self.forward_jumps = 0

    # -- reading state -----------------------------------------------------
    @property
    def physical_ms(self) -> int:
        return self._physical_ms

    @property
    def logical(self) -> int:
        return self._logical

    def stamp(self) -> Stamp:
        return Stamp(self._physical_ms, self._logical, self.node)

    def wall_ms(self) -> int:
        return self._wall_ms()

    def skew_ms(self) -> int:
        """How far the clock is ahead of the wall: 0 means "no help needed"."""
        return self._physical_ms - self._wall_ms()

    def is_drifting(self) -> bool:
        if self.max_skew_ms is None:
            return self.skew_ms() > 0
        return self.skew_ms() > self.max_skew_ms

    def check_skew(self) -> None:
        if self.max_skew_ms is None:
            return
        skew = self.skew_ms()
        if skew > self.max_skew_ms:
            raise ClockError(
                f"clock {self.node} is {skew} ms ahead of its wall clock, "
                f"past the {self.max_skew_ms} ms bound: the wall clock is the broken one"
            )

    # -- the two transitions ----------------------------------------------
    def now(self) -> Stamp:
        """A local event: never behind the last stamp, never behind the wall."""
        self.events += 1
        wall = self._wall_ms()
        if wall > self._physical_ms:
            self._physical_ms = wall
            self._logical = 0
            self.forward_jumps += 1
        else:
            # Either the wall stood still or it went backwards. Both land here,
            # and the counter is what keeps the order strict.
            self._logical += 1
        return self.stamp()

    def send(self) -> Stamp:
        """Sending is a local event; the stamp travels with the message."""
        return self.now()

    def receive(self, remote: Stamp) -> Stamp:
        """Fold a remote stamp in, then stamp the receipt after it."""
        if not isinstance(remote, Stamp):
            raise ClockError(f"receive takes a Stamp, not {type(remote).__name__}")
        self.receives += 1
        wall = self._wall_ms()
        physical = max(self._physical_ms, remote.physical_ms, wall)
        if physical == self._physical_ms == remote.physical_ms:
            logical = max(self._logical, remote.logical) + 1
        elif physical == self._physical_ms:
            logical = self._logical + 1
        elif physical == remote.physical_ms:
            logical = remote.logical + 1
        else:
            # The wall clock overtook both clocks, so this is a fresh millisecond
            # for us even though it is not a new event in the system.
            logical = 0
            self.forward_jumps += 1
        self._physical_ms = physical
        self._logical = logical
        return self.stamp()
