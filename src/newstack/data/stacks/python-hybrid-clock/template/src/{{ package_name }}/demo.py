"""Six claims about hybrid clocks, each one measured on the same small world."""

from __future__ import annotations

from dataclasses import dataclass

from .audit import causality_breaks, disagreements, order_by_stamp, order_by_wall
from .clock import ClockError, HybridClock, ManualWall
from .stamp import Stamp
from .world import World

START_MS = 1_700_000_000_000


@dataclass(frozen=True)
class Story:
    title: str
    lines: list[str]
    held: bool

    def render(self) -> str:
        mark = "holds" if self.held else "BROKEN"
        body = "\n".join(f"  {line}" for line in self.lines)
        return f"{self.title}\n{body}\n  -> {mark}\n"


def backward_wall() -> Story:
    """A wall clock that steps back must not move the stamp back."""
    wall = ManualWall(START_MS)
    clock = HybridClock("a", wall_ms=wall.now)
    first = clock.now()
    wall.set(START_MS - 400)
    second = clock.now()
    third = clock.now()
    lines = [
        f"wall {START_MS}                 -> {first.text()}",
        f"wall {START_MS - 400} (stepped back) -> {second.text()}",
        f"wall {START_MS - 400} (again)        -> {third.text()}",
        f"the stamps still increase: {first < second < third}",
        f"the counter carried the order: {second.logical} then {third.logical}",
    ]
    return Story("1. a wall clock that steps backwards cannot move a stamp", lines,
                 first < second < third)


def message_not_in_the_past() -> Story:
    """A slow node must not stamp a receipt before the send it answers."""
    world = World({"a": 500, "b": 0})
    world.tick(0)
    sent, received = world.send("a", "b", "ping")
    lines = [
        f"a runs 500 ms fast: its wall reads {world.wall('a').now()}",
        f"b's wall reads {world.wall('b').now()}, so on the wall the receipt came first",
        f"send    {sent.text()}",
        f"receive {received.text()}",
        f"the receipt is later by stamp: {sent < received}",
    ]
    return Story("2. a message cannot arrive before it was sent", lines, sent < received)


def naive_order() -> Story:
    """Sorting by the wall clock puts a receipt before its own send."""
    world = World({"a": 500, "b": 0})
    world.tick(0)
    world.local("b", "before")
    world.send("a", "b", "ping")
    world.local("b", "after")
    entries = world.entries
    by_wall = [
        f"{entry.kind:<8}{entry.node} wall {entry.wall_ms}" for entry in order_by_wall(entries)
    ]
    by_stamp = [
        f"{entry.kind:<8}{entry.node} {entry.stamp.text()}" for entry in order_by_stamp(entries)
    ]
    inversions = disagreements(entries)
    breaks = causality_breaks(world.messages)
    lines = ["wall order:", *(f"  {line}" for line in by_wall),
             "stamp order:", *(f"  {line}" for line in by_stamp),
             f"inversions between the two orders: {len(inversions)}",
             f"causal breaks under the stamp order: {len(breaks)}"]
    return Story("3. the wall order and the stamp order disagree", lines,
                 bool(inversions) and not breaks)


def total_order() -> Story:
    """Two events in the same millisecond still have one order."""
    left = Stamp(START_MS, 0, "alpha")
    right = Stamp(START_MS, 0, "beta")
    without = [left.text(), right.text()]
    ordered = sorted([right, left])
    reversed_order = sorted([left, right])
    lines = [
        f"same millisecond, same counter: {without[0]} and {without[1]}",
        "without the node they are the same point, so any order is defensible",
        f"sorted: {ordered[0].text()} then {ordered[1].text()}",
        f"sorted the other way round, same answer: {reversed_order == ordered}",
    ]
    return Story("4. the node name makes the order total", lines, reversed_order == ordered)


def skew_is_measured() -> Story:
    """Skew is a number, and a bound turns it into a refusal."""
    world = World({"a": 500, "b": 0}, max_skew_ms=400)
    world.tick(0)
    world.send("a", "b", "ping")
    clock_b = world.clock("b")
    skew = clock_b.skew_ms()
    refused = ""
    try:
        clock_b.check_skew()
    except ClockError as error:
        refused = str(error)
    lines = [
        f"b's wall reads {clock_b.wall_ms()}, its physical clock reads {clock_b.physical_ms}",
        f"skew {skew} ms against a bound of {clock_b.max_skew_ms} ms",
        f"drifting: {clock_b.is_drifting()}",
        f"refusal: {refused}",
    ]
    return Story("5. skew is a number, so a bound can refuse it", lines,
                 skew == 500 and bool(refused))


def gossip_converges() -> Story:
    """After one exchange each clock is at least as high as everything it saw."""
    world = World({"a": 0, "b": 250, "c": -120})
    world.tick(0)
    world.local("c", "first")
    world.tick(40)
    world.local("a", "second")
    world.send("a", "b")
    world.send("b", "c")
    world.send("c", "a")
    highest = max(entry.stamp for entry in world.entries)
    lows = {node: world.clock(node).physical_ms for node in world.clocks}
    converged = all(clock.physical_ms >= highest.physical_ms for clock in world.clocks.values())
    lines = [
        f"highest stamp in the world: {highest.text()}",
        "physical clock per node: "
        + ", ".join(f"{node}={value}" for node, value in sorted(lows.items())),
        f"every node reached it: {converged}",
        f"causal breaks: {len(causality_breaks(world.messages))}",
    ]
    return Story("6. one exchange lifts every clock to what it saw", lines, converged)


def stories() -> list[Story]:
    return [
        backward_wall(),
        message_not_in_the_past(),
        naive_order(),
        total_order(),
        skew_is_measured(),
        gossip_converges(),
    ]


def render() -> str:
    return "".join(story.render() + "\n" for story in stories())
