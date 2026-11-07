"""Six stories about slots, cursors, and what a ring owes its drain.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import drop_oldest_view
from .corpus import synthetic
from .ring import RingBuffer


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the buffer makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    ring = RingBuffer(16, corpus)

    ordered = list(ring.contents()) == list(drop_oldest_view(16, corpus))
    first = Story(
        "the drain is the reference deque, exactly",
        f"{len(corpus)} pushes, deque-equal={ordered}",
        ordered and ring.invariant(),
    )

    cursor = ring.invariant() and 0 <= ring.tail < ring.capacity
    second = Story(
        "the cursor never lands outside [0, capacity)",
        f"head {ring.head} tail {ring.tail} of {ring.capacity} slots",
        cursor,
    )

    oldest = ring.peek() == drop_oldest_view(16, corpus)[0]
    third = Story(
        "a full ring overwrites exactly the oldest",
        f"oldest {ring.peek()}, overwrites {ring.overwrites}",
        oldest and ring.full,
    )

    kept = list(drop_oldest_view(16, corpus))
    drained = ring.drain()
    fourth = Story(
        "a drain empties the ring and parks the cursor",
        f"{len(drained)} out, head {ring.head}, count {len(ring)}",
        drained == kept and len(ring) == 0 and ring.head == 0,
    )

    lone = RingBuffer(1, [7, 8, 9])
    lone_out = lone.drain()
    fifth = Story(
        "capacity one keeps only the newest",
        f"drain {lone_out}, overwrites {lone.overwrites}",
        lone.capacity == 1 and lone_out == [9] and lone.overwrites == 2,
    )

    probe = RingBuffer(4)
    for value in range(6):
        probe.push(value)
    sixth = Story(
        "the walk survives the wrap, recomputed each time",
        f"contents {probe.contents()} of last four, audit {probe.audit()}",
        probe.contents() == (2, 3, 4, 5) and not probe.audit(),
    )
    return [first, second, third, fourth, fifth, sixth]
