"""Seeded storms of pushes, pops, and decreases, replayed as a sort.

The workload is the falsifiable part: a heap that survives a seeded
stream of mixed moves must pop exactly the sorted sequence of the
keys it still holds, keep every degree under the documented log
bound, and answer a decrease-key without breaking heap order — the
audit walks the raw forest after every single move, never at the end.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .heap import FibonacciHeap, degree_bound

STEPS = 140


class WorkloadError(ValueError):
    """The storm was asked for in sizes it cannot hold."""


@dataclass(frozen=True)
class Replay:
    """What a storm spent and whether it ever disagreed with the sort."""

    steps: int
    checks: int
    breaks: int
    pops: int
    decreases: int
    max_degree: int
    bound: int
    seated: bool
    exact: bool


def run_storm(seed: int = 13, steps: int = STEPS) -> Replay:
    """Push, decrease, and pop a seeded stream, auditing every move.

    Pops drain the smallest, so the ledger drops exactly the key the
    heap released; a stale-handle push would double-count a live key
    and the equality below would report the storm broken.
    """
    if not isinstance(seed, int) or not isinstance(steps, int) or steps < 1:
        raise WorkloadError("a storm needs whole-number bounds")
    heap = FibonacciHeap()
    rng = random.Random(seed)
    live: dict[int, int] = {}
    checks = 0
    breaks = 0
    pops = 0
    decreases = 0
    max_degree = 0
    peak = 0
    for step in range(steps):
        move = rng.randrange(6)
        if move <= 1 or not live or step < 5:
            key = rng.randint(-5000, 5000)
            handle = heap.push(key)
            live[handle.token] = key
        elif move in (2, 3):
            token = rng.choice(sorted(live))
            new_key = rng.randint(-5000, live[token])
            heap.decrease(heap._handles[token], new_key)
            live[token] = new_key
            decreases += 1
        else:
            if heap.audit():
                breaks += 1
            smallest = heap.peek()
            heap.pop_min()
            pops += 1
            owner = next((t for t, v in live.items() if v == smallest), None)
            if owner is None:
                breaks += 1
            else:
                del live[owner]
        degrees = heap.degrees()
        max_degree = max([max_degree, *degrees], default=max_degree)
        peak = max(peak, len(live))
        checks += 1
        if heap.keys() != sorted(live.values()) or heap.audit():
            breaks += 1
    drained = [heap.pop_min() for _ in range(len(heap))]
    checks += 1
    exact = drained == sorted(live.values())
    bound = degree_bound(max(peak, 1))
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        pops=pops,
        decreases=decreases,
        max_degree=max_degree,
        bound=bound,
        seated=max_degree <= bound and breaks == 0,
        exact=exact,
    )


def replay_matches(keys: list[int]) -> bool:
    """A quiet heap pops exactly the plain sort, no storm involved."""
    heap = FibonacciHeap(keys)
    return [heap.pop_min() for _ in range(len(heap))] == sorted(keys)


def decrease_holds(keys: list[int], slot: int, new_key: int) -> bool:
    """A decrease-key lands the forest back inside heap order."""
    heap = FibonacciHeap()
    ledger: dict[int, int] = {}
    for key in keys:
        handle = heap.push(key)
        ledger[handle.token] = key
    if not ledger:
        return False
    target = sorted(ledger)[slot % len(ledger)]
    if new_key > ledger[target]:
        return False
    heap.decrease(heap._handles[target], new_key)
    ledger[target] = new_key
    return heap.keys() == sorted(ledger.values()) and heap.invariant()


