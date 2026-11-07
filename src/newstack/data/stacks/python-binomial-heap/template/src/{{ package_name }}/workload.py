"""Seeded storms of pushes, pop-mins, and melds, checked every step.

The workload is the falsifiable part: a forest that keeps its shape
through 160 seeded ops must answer exactly ``sorted(corpus)``, must
hold rank-k trees of 2^k keys and one tree per rank after every op,
and must size itself by the bit pattern of the count it holds.
"""

from __future__ import annotations

from dataclasses import dataclass

from .heap import BinomialHeap, ranks_of
from .streams import monotone, synthetic

STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for in sizes it cannot hold."""


@dataclass(frozen=True)
class Replay:
    """What a storm spent, and whether the forest ever lied."""

    steps: int
    checks: int
    links: int
    melds: int
    breaks: int
    sorted_held: bool
    shapes_held: bool


def run_workload(seed: int = 13, steps: int = STEPS) -> Replay:
    """Push, pop-min, and meld a seeded stream, checking after every op."""
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 1:
        raise WorkloadError("a storm needs whole-number bounds")
    corpus = synthetic(steps, seed=seed)
    heap = BinomialHeap()
    side = BinomialHeap()
    pool: list[int] = []
    answered: list[int] = []
    checks = 0
    breaks = 0
    for index in range(steps):
        heap.push(*corpus[index])
        pool.append(corpus[index][0])
        checks += 1
        if not heap.invariant() or heap.shape() != ranks_of(len(heap)):
            breaks += 1
            break
        if index % 3 == 2:
            side.push(corpus[index][0] + 1_000_000, None)
            pool.append(corpus[index][0] + 1_000_000)
            heap.meld(side)
            checks += 1
            if not heap.invariant() or heap.shape() != ranks_of(len(heap)):
                breaks += 1
                break
        if index % 3 and heap:
            answered.append(heap.pop()[0])
            checks += 1
            if not heap.invariant() or heap.shape() != ranks_of(len(heap)):
                breaks += 1
                break
    while heap:
        checks += 1
        answered.append(heap.pop()[0])
        if not heap.invariant():
            breaks += 1
            break
    return Replay(
        steps,
        checks,
        heap.links,
        heap.melds,
        breaks,
        sorted(answered) == sorted(pool),
        heap.shape() == ranks_of(0),
    )


def run_meld(seed: int = 11, left: int = 50, right: int = 37) -> Replay:
    """Two forests meld, then drain: sorted concat is the only answer."""
    if not isinstance(seed, int) or left < 1 or right < 1:
        raise WorkloadError("a meld needs whole-number bounds")
    one = BinomialHeap()
    two = BinomialHeap()
    for pair in synthetic(left, seed=seed):
        one.push(*pair)
    for pair in synthetic(right, seed=seed + 1):
        two.push(*pair)
    truth = sorted(
        [key for key, _ in synthetic(left, seed=seed)]
        + [key for key, _ in synthetic(right, seed=seed + 1)]
    )
    one.meld(two)
    held = one.shape() == ranks_of(len(one)) and one.invariant()
    answered = list(one.pop_all())
    return Replay(
        left + right,
        left + right + 2,
        one.links,
        one.melds,
        0 if held and not two else 1,
        answered == truth,
        held,
    )


def run_monotone(seed: int = 11, size: int = 64) -> Replay:
    """A rising stream: the forest still shapes itself by the bits."""
    if not isinstance(seed, int) or size < 1:
        raise WorkloadError("a stream needs whole-number bounds")
    stream = monotone(size, seed=seed)
    heap = BinomialHeap()
    checks = 0
    breaks = 0
    for key, value in stream:
        heap.push(key, value)
        checks += 1
        if not heap.invariant() or heap.shape() != ranks_of(len(heap)):
            breaks += 1
            break
    drained = list(heap.pop_all())
    return Replay(
        size,
        checks + size,
        heap.links,
        heap.melds,
        breaks,
        drained == sorted(key for key, _ in stream),
        heap.shape() == ranks_of(0),
    )
