"""Seeded storms of pushes and pops, checked after every move.

The storm is the falsifier with a memory: it drives a ring through a
scripted sequence of pushes, pops, peeks, and drains, and after every
step it re-checks the recomputed walk against the reference deque,
the cursor against `[0, capacity)`, and the drop against the oldest.
A break counter the storm cannot push past zero is the only report
here worth printing.
"""

from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass

from .brute import drop_oldest_view, storm_reference
from .corpus import DEFAULT_SEED
from .ring import RingBuffer, RingError
from .values import MAX_VALUE, ensure_value

DEFAULT_STEPS = 140


class StormError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any answer it took was wrong."""

    steps: int
    checks: int
    breaks: int
    pushes: int
    pops: int
    drains: int
    overwrites: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def _operations(steps: int, capacity: int, seed: int) -> list[tuple[str, int | None]]:
    if steps <= 0:
        raise StormError(f"no storm of {steps} steps")
    if capacity < 1:
        raise StormError(f"no storm of capacity {capacity}")
    rng = random.Random(seed)
    script: list[tuple[str, int | None]] = []
    for _ in range(steps):
        roll = rng.random()
        if roll < 0.55:
            script.append(("push", rng.randint(-MAX_VALUE, MAX_VALUE)))
        elif roll < 0.85:
            script.append(("pop", None))
        elif roll < 0.95:
            script.append(("peek", None))
        else:
            script.append(("drain", None))
    return script


def _settle(ring: RingBuffer, seats: list[int]) -> tuple[int, int]:
    """Breaks this position owes, and the checks it spent to find them."""
    breaks = 0
    checks = 4
    if list(ring.contents()) != seats:
        breaks += 1
    if not ring.invariant():
        breaks += 1
    if ring.audit():
        breaks += 1
    if ring.full and seats and ring.peek() != seats[0]:
        breaks += 1
    return breaks, checks


def run_storm(
    steps: int = DEFAULT_STEPS, capacity: int = 8, seed: int = DEFAULT_SEED
) -> Replay:
    """Drive the storm, re-checking the ring against the deque each step."""
    script = _operations(steps, capacity, seed)
    ring = RingBuffer(capacity)
    seats: list[int] = []
    breaks = 0
    checks = 0
    pushes = pops = drains = 0
    for verb, value in script:
        if verb == "push":
            assert value is not None
            ensure_value(value)
            if ring.push(value) is not None:
                seats.pop(0)
            seats.append(value)
            pushes += 1
        elif verb == "pop":
            if len(ring):
                if ring.pop() != seats.pop(0):
                    breaks += 1
                pops += 1
            else:
                with contextlib.suppress(RingError):
                    ring.pop()
                    breaks += 1
        elif verb == "peek":
            if len(ring):
                if ring.peek() != seats[0]:
                    breaks += 1
            else:
                with contextlib.suppress(RingError):
                    ring.peek()
                    breaks += 1
        else:
            drains += 1
            if ring.drain() != seats:
                breaks += 1
            seats.clear()
        checks += 1
        settle_breaks, settle_checks = _settle(ring, seats)
        breaks += settle_breaks
        checks += settle_checks
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        pushes=pushes,
        pops=pops,
        drains=drains,
        overwrites=ring.overwrites,
        seated=ring.invariant() and list(ring.contents()) == seats,
    )


def drain_matches(capacity: int, values: list[int]) -> bool:
    """The ring drains exactly what the deque drains, pushes only."""
    ring = RingBuffer(capacity, values)
    return ring.drain() == list(drop_oldest_view(capacity, values))


def storm_matches(capacity: int, seed: int) -> bool:
    """The ring's answers are the deque's answers, move for move."""
    script = _operations(DEFAULT_STEPS, capacity, seed)
    ring = RingBuffer(capacity)
    answers: list[int] = []
    for verb, value in script:
        if verb == "push":
            ring.push(value)
        elif verb == "pop" and len(ring):
            answers.append(ring.pop())
        elif verb == "drain":
            answers.extend(ring.drain())
    return answers == storm_reference(capacity, script)
