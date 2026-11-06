"""Mixed and monotone storms, replayed against the sorted truth.

The workload is the falsifiable part: a heap that keeps its answer
through 160 seeded pushes and pop-mins must return exactly
``sorted(corpus)``, must keep every bucket invariant after every op,
and must spend zero rebuilds on a stream that never steps back.
"""

from __future__ import annotations

from dataclasses import dataclass

from .heap import RadixHeap
from .streams import monotone, synthetic

STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for in sizes it cannot hold."""


@dataclass(frozen=True)
class Replay:
    """What a storm spent and whether it ever lied."""

    steps: int
    checks: int
    rebuilds: int
    breaks: int
    sorted_held: bool


def run_workload(seed: int = 13, steps: int = STEPS) -> Replay:
    """Push and pop-min a seeded mixed stream, checking after every op."""
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 1:
        raise WorkloadError("a storm needs whole-number bounds")
    corpus = synthetic(steps, seed=seed)
    truth = sorted(key for key, _ in corpus)
    heap = RadixHeap()
    checks = 0
    breaks = 0
    for index in range(steps):
        heap.push(*corpus[index])
        checks += 1
        if not heap.invariant():
            breaks += 1
            break
        if index % 3 and heap:
            heap.pop()
            checks += 1
            if not heap.invariant():
                breaks += 1
                break
    while heap:
        checks += 1
        heap.pop()
        if not heap.invariant():
            breaks += 1
            break
    held = RadixHeap()
    for pair in corpus:
        held.push(*pair)
    return Replay(steps, checks, heap.rebuilds, breaks, list(held.pop_all()) == truth)


def run_monotone(seed: int = 11, size: int = 64) -> Replay:
    """A stream that never steps back spends no rebuild and answers sorted."""
    if not isinstance(seed, int) or not isinstance(size, int) or size < 1:
        raise WorkloadError("a stream needs whole-number bounds")
    stream = monotone(size, seed=seed)
    heap = RadixHeap()
    checks = 0
    breaks = 0
    for key, value in stream:
        heap.push(key, value)
        checks += 1
        if not heap.invariant():
            breaks += 1
            break
    drained = list(heap.pop_all())
    checks += size
    return Replay(size, checks, heap.rebuilds, breaks,
                  drained == sorted(key for key, _ in stream))
