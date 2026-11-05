"""A small world of nodes with their own wall clocks, so skew is a value."""

from __future__ import annotations

from dataclasses import dataclass

from .clock import HybridClock, ManualWall
from .stamp import Stamp

DEFAULT_START_MS = 1_700_000_000_000


class WorldError(ValueError):
    """A plan that cannot be carried out, said out loud."""


@dataclass(frozen=True)
class Entry:
    """One thing that happened, with the stamp the clock produced for it."""

    kind: str
    node: str
    stamp: Stamp
    wall_ms: int = 0
    detail: str = ""

    def line(self) -> str:
        tail = f"  {self.detail}" if self.detail else ""
        return f"{self.kind:<9} {self.node:<8} {self.stamp.text()}{tail}"


class World:
    """Nodes, their offsets from true time, and the events they perform.

    The offset is the whole point: two nodes running the same code disagree about
    "now" by however much their clocks have drifted, and the hybrid clock is
    supposed to keep causality intact anyway.
    """

    def __init__(
        self,
        offsets: dict[str, int] | None = None,
        *,
        start_ms: int = DEFAULT_START_MS,
        max_skew_ms: int | None = None,
    ) -> None:
        if offsets is None:
            offsets = {"a": 0, "b": 0, "c": 0}
        if not offsets:
            raise WorldError("a world needs at least one node")
        self.true_ms = start_ms
        self.offsets = dict(offsets)
        self.walls = {node: ManualWall(start_ms + offset) for node, offset in self.offsets.items()}
        self.clocks = {
            node: HybridClock(node, wall_ms=wall.now, max_skew_ms=max_skew_ms)
            for node, wall in self.walls.items()
        }
        self.entries: list[Entry] = []
        self.messages: list[tuple[Stamp, Stamp]] = []

    # -- node lookup -------------------------------------------------------
    def clock(self, node: str) -> HybridClock:
        try:
            return self.clocks[node]
        except KeyError as error:
            known = ", ".join(sorted(self.clocks))
            raise WorldError(f"unknown node {node!r}; this world has {known}") from error

    def wall(self, node: str) -> ManualWall:
        try:
            return self.walls[node]
        except KeyError as error:
            known = ", ".join(sorted(self.walls))
            raise WorldError(f"unknown node {node!r}; this world has {known}") from error

    # -- time --------------------------------------------------------------
    def tick(self, ms: int = 1) -> None:
        """Let true time pass on every node at once, offsets preserved."""
        if ms < 0:
            raise WorldError(f"time does not run backwards here, not {ms}")
        self.true_ms += ms
        for node, offset in self.offsets.items():
            self.walls[node].set(self.true_ms + offset)

    def step_back(self, node: str, ms: int) -> None:
        """The failure this stack exists for: one wall clock jumps backwards."""
        if ms <= 0:
            raise WorldError(f"a step back must be positive, not {ms}")
        self.walls[node].set(self.walls[node].now() - ms)

    # -- events ------------------------------------------------------------
    def local(self, node: str, detail: str = "") -> Stamp:
        wall = self.wall(node).now()
        stamp = self.clock(node).now()
        self.entries.append(Entry("local", node, stamp, wall, detail))
        return stamp

    def send(self, source: str, target: str, detail: str = "") -> tuple[Stamp, Stamp]:
        wall = self.wall(source).now()
        sent = self.clock(source).send()
        self.entries.append(Entry("send", source, sent, wall, f"-> {target} {detail}".strip()))
        received = self.clock(target).receive(sent)
        self.entries.append(Entry("receive", target, received, self.wall(target).now(),
                                  f"<- {source}"))
        self.messages.append((sent, received))
        if not sent < received:
            raise WorldError(
                f"message {source}->{target} stamped {sent.text()} arrived as "
                f"{received.text()}, which is not later: the clock lost an event"
            )
        return sent, received

    def deliver(self, source: str, target: str, stamp: Stamp) -> Stamp:
        """Deliver a stamp that was produced earlier, e.g. over a slow network."""
        received = self.clock(target).receive(stamp)
        self.entries.append(Entry("receive", target, received, self.wall(target).now(),
                                  f"<- {source} (delayed)"))
        self.messages.append((stamp, received))
        return received

    # -- reporting ---------------------------------------------------------
    def reports(self) -> list[str]:
        lines = [
            f"{'node':<8}{'physical_ms':>20}{'logical':>9}{'wall_ms':>20}{'skew_ms':>9}"
        ]
        for node in sorted(self.clocks):
            clock = self.clocks[node]
            lines.append(
                f"{node:<8}{clock.physical_ms:>20}{clock.logical:>9}"
                f"{clock.wall_ms():>20}{clock.skew_ms():>9}"
            )
        return lines

    def max_skew(self) -> int:
        return max((clock.skew_ms() for clock in self.clocks.values()), default=0)

    def violations(self) -> list[str]:
        """Every place where a message arrived before it was sent."""
        return [
            f"{sent.text()} -> {received.text()}"
            for sent, received in self.messages
            if not sent < received
        ]

    def stamp_lines(self) -> list[str]:
        return [entry.line() for entry in self.entries]

    def as_dict(self) -> dict:
        return {
            "true_ms": self.true_ms,
            "nodes": {
                node: {
                    "offset_ms": self.offsets[node],
                    "physical_ms": clock.physical_ms,
                    "logical": clock.logical,
                    "wall_ms": clock.wall_ms(),
                    "skew_ms": clock.skew_ms(),
                    "events": clock.events,
                    "receives": clock.receives,
                }
                for node, clock in sorted(self.clocks.items())
            },
            "messages": len(self.messages),
            "violations": self.violations(),
        }
