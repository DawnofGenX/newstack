"""A Lamport clock gives every event a number, and the number is all it gives.

Two replicas that never spoke still get an order out of it. That is the trade: a
Lamport order is total, cheap (one integer), and unable to tell "this happened after
that" from "these two happened at the same time on replicas that had not met". The
demo keeps one interleaving and reverses it, and the order of the same two events
comes out reversed - which is what an artifact looks like.
"""

from __future__ import annotations

from dataclasses import dataclass


class LamportError(ValueError):
    """A stamp or event that cannot be built."""


@dataclass(frozen=True, order=True)
class Stamp:
    """One clock reading, plus the node that read it (so ties have a name)."""

    time: int
    node: str

    def __post_init__(self) -> None:
        if isinstance(self.time, bool) or not isinstance(self.time, int):
            raise LamportError(f"a stamp time is a whole number, not {self.time!r}")
        if self.time < 0:
            raise LamportError(f"a stamp time cannot be negative: {self.time}")
        if not isinstance(self.node, str) or not self.node:
            raise LamportError("a stamp needs a node name")

    def text(self) -> str:
        return f"{self.time:04d}@{self.node}"


class LamportClock:
    """One integer per node: tick forward, and on receive take the larger plus one."""

    def __init__(self, node: str) -> None:
        if not isinstance(node, str) or not node:
            raise LamportError("a clock needs a node name")
        self.node = node
        self.time = 0
        self.ticks = 0
        self.receives = 0

    def tick(self) -> Stamp:
        """A local event."""
        self.time += 1
        self.ticks += 1
        return Stamp(self.time, self.node)

    def send(self) -> Stamp:
        """A send is an event in the sender's own timeline."""
        return self.tick()

    def receive(self, stamp: Stamp) -> Stamp:
        """A receive is later than both the message and anything local before it."""
        self.time = max(self.time, stamp.time) + 1
        self.receives += 1
        return Stamp(self.time, self.node)


@dataclass(frozen=True)
class Event:
    """A named event with the stamp it was given."""

    name: str
    stamp: Stamp
    note: str = ""

    def text(self) -> str:
        tail = f"  {self.note}" if self.note else ""
        return f"{self.stamp.text()}  {self.name}{tail}"


def order(events: list[Event]) -> list[Event]:
    """The total order a Lamport clock gives: by time, then by node name.

    The node-name tiebreak is not a fact about the events. It is a convention that
    makes the order deterministic, which is the most a total order can promise.
    """
    if not events:
        raise LamportError("there is no order of no events")
    return sorted(events, key=lambda event: (event.stamp.time, event.stamp.node))


def busy(node: str, ticks: int) -> LamportClock:
    """A clock that has already counted `ticks` local events it will never mention.

    Unrelated local work is invisible to a Lamport clock: it only makes the next stamp
    bigger. That is why the order of two events from replicas that never met follows
    the work each replica happened to do, not anything about the events.
    """
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 0:
        raise LamportError(f"a busy clock takes a whole number of ticks, not {ticks!r}")
    clock = LamportClock(node)
    for _ in range(ticks):
        clock.tick()
    return clock


def precedes(earlier: Event, later: Event) -> bool:
    """Whether the total order puts `earlier` first. Exact, and only about the stamps."""
    first, second = order([earlier, later])
    return first is earlier and second is later
