"""Compare what the hybrid clock says with what a wall clock would have said."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from .stamp import Stamp
from .world import Entry, World


class AuditError(ValueError):
    """An audit that cannot be answered from the evidence it was given."""


def order_by_stamp(entries: list[Entry]) -> list[Entry]:
    """The hybrid order: physical, then logical, then node."""
    return sorted(entries, key=lambda entry: entry.stamp.key())


def order_by_wall(entries: list[Entry]) -> list[Entry]:
    """The order a naive implementation gets: sort by the local wall clock."""
    return sorted(entries, key=lambda entry: (entry.wall_ms, entry.node))


def is_strictly_increasing(stamps: list[Stamp]) -> bool:
    return all(earlier < later for earlier, later in itertools.pairwise(stamps))


@dataclass(frozen=True)
class Disagreement:
    """One pair of events the two orderings place differently."""

    left: Entry
    right: Entry

    def line(self) -> str:
        return (
            f"{self.left.kind} on {self.left.node} and {self.right.kind} on {self.right.node}: "
            f"the wall says {self.left.wall_ms} then {self.right.wall_ms}, "
            f"the stamps say {self.left.stamp.text()} then {self.right.stamp.text()}"
        )


def disagreements(entries: list[Entry]) -> list[Disagreement]:
    """Every inversion between wall order and stamp order.

    An inversion is not automatically a bug: two genuinely concurrent events may
    be ordered either way. What is a bug is an inversion across a message, which
    :func:`causality_breaks` looks for.
    """
    by_stamp = {id(entry): index for index, entry in enumerate(order_by_stamp(entries))}
    by_wall = {id(entry): index for index, entry in enumerate(order_by_wall(entries))}
    found: list[Disagreement] = []
    for left_index, left in enumerate(entries):
        for right in entries[left_index + 1 :]:
            left_before_stamp = by_stamp[id(left)] < by_stamp[id(right)]
            left_before_wall = by_wall[id(left)] < by_wall[id(right)]
            if left_before_stamp != left_before_wall:
                found.append(Disagreement(left, right))
    return found


def causality_breaks(pairs: list[tuple[Stamp, Stamp]]) -> list[str]:
    """Pairs where a receipt is stamped before the send it answers.

    This is the only failure that matters: a wall-clock order can be wrong
    without anybody noticing, but a clock that stamps a reply before its request
    has lost an event that provably happened.
    """
    return [
        f"{sent.text()} -> {received.text()}"
        for sent, received in pairs
        if not sent < received
    ]


def coverage(world: World) -> dict[str, int]:
    """How much each node has heard: events, receipts, and wall jumps."""
    return {
        node: {
            "events": clock.events,
            "receives": clock.receives,
            "forward_jumps": clock.forward_jumps,
            "skew_ms": clock.skew_ms(),
        }
        for node, clock in sorted(world.clocks.items())
    }


def monotone(entries: list[Entry]) -> bool:
    """True when each node's own stamps never go backwards."""
    per_node: dict[str, list[Stamp]] = {}
    for entry in entries:
        per_node.setdefault(entry.node, []).append(entry.stamp)
    return all(is_strictly_increasing(stamps) for stamps in per_node.values())
