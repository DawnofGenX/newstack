"""Seeded storms of pushes and pops, checked after every move.

The workload is the falsifier with a memory: it drives a heap
through a scripted sequence of pushes, pops, and peeks, and after
every step it re-checks the array against the parent rule and the
peek against the minimum of the live multiset. A break counter the
storm cannot push past zero is the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .heap import MinHeap
from .keys import ensure_key
from .oracle import brute_drain, heap_breaks

DEFAULT_STEPS = 140


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any promise it watched broke."""

    steps: int
    checks: int
    breaks: int
    pushes: int
    pops: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 40
) -> Replay:
    """Push, pop, peek; re-check everything after every move.

    The live bag is the dumb shadow: a plain Python list the storm
    sorts whenever it needs an answer. The heap may disagree with its
    own shadow only by being wrong, and every disagreement lands in
    the break counter. Draining at the end must spell the plain sort
    of everything still live — that equality is the product.
    """
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    pool_keys = synthetic(pool, seed=seed)
    heap = MinHeap()
    live: list[int] = []
    breaks = 0
    checks = 0
    pushes = 0
    pops = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.55 or not live:
            key = ensure_key(rng.choice(pool_keys))
            heap.push(key)
            live.append(key)
            pushes += 1
        else:
            got = heap.pop()
            live.remove(got)
            pops += 1
        checks += 2
        if heap_breaks(heap.array()):
            breaks += 1  # the parent rule broke under the storm
        if live and heap.peek() != min(live):
            breaks += 1  # the head is not the minimum of the bag
        checks += 1
    drain = heap.drain()
    checks += 1
    if drain != brute_drain(live):
        breaks += 1  # the drain is not the plain sort of what lived
    if heap_breaks(heap.array()):
        breaks += 1  # an emptied heap still owes the parent rule
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        pushes=pushes,
        pops=pops,
        seated=not heap and drain == brute_drain(live),
    )


def rebuild_matches(keys: list[int]) -> bool:
    """A heap rebuilt from its own array answers the drain alike."""
    heap = MinHeap(keys)
    rebuilt = MinHeap(heap.array())
    return rebuilt.drain() == brute_drain(keys)
