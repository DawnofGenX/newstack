"""Six stories about the forest, every figure computed as it is told.

A story is a claim the heap must keep while the story runs: pops
replay the sort, a decrease lands inside heap order, the cascade
clears the table, debts stay paid, the edges answer quietly, and a
storm ends where the sort says it ends. Nothing here is remembered
from a previous run.
"""

from __future__ import annotations

from dataclasses import dataclass

from .brute import expose, naive_sort
from .corpus import synthetic
from .heap import FibonacciHeap, Handle
from .workload import run_storm


@dataclass(frozen=True)
class Story:
    """One claim, the detail that sizes it, and whether it held."""

    title: str
    detail: str
    held: bool


def _forest_orders() -> Story:
    keys = [9, -4, 17, 0, 17, 61, -4]
    heap = FibonacciHeap(keys)
    drained = [heap.pop_min() for _ in range(len(heap))]
    return Story(
        "pops replay the plain sort",
        f"{keys} drained to {drained}",
        drained == naive_sort(keys),
    )


def _a_key_drops() -> Story:
    heap = FibonacciHeap()
    ledger: dict[int, int] = {}
    tracked: dict[int, Handle] = {}
    for key in (500, 60, 90, 40):
        handle = heap.push(key)
        ledger[handle.token] = key
        tracked[handle.token] = handle
    target = max(ledger, key=lambda token: ledger[token])
    heap.decrease(tracked[target], -13)
    ledger[target] = -13
    return Story(
        "decrease-key retunes a tracked item",
        f"peek after dropping item {target} to -13: {heap.peek()}",
        heap.peek() == -13 and heap.keys() == sorted(ledger.values()),
    )


def _the_cascade_runs() -> Story:
    heap = FibonacciHeap()
    handles = [heap.push(key) for key in (1, 2, 3, 4, 5, 6, 7, 8)]
    for handle in handles[1:]:
        heap.decrease(handle, -handle.token)
    drained = [heap.pop_min() for _ in range(len(heap))]
    return Story(
        "cascading cuts keep every degree small",
        f"seven decreases, drained {drained}",
        drained == sorted([1, *(-handle.token for handle in handles[1:])])
        and heap.invariant(),
    )


def _debts_stay_paid() -> Story:
    keys = synthetic(48, seed=11)
    heap = FibonacciHeap(keys)
    for _ in range(12):
        heap.pop_min()
    holds = heap.invariant() and expose(heap) == heap.keys()
    return Story(
        "the audit walks raw links, not stored figures",
        f"48 keys, 12 pops, audit faults: {len(heap.audit())}",
        holds,
    )


def _the_edges_answer() -> Story:
    bare = FibonacciHeap()
    quiet = bare.keys() == [] and len(bare) == 0
    one = FibonacciHeap([7])
    solo = one.peek() == 7 and one.pop_min() == 7 and len(one) == 0
    return Story(
        "empty and single answer quietly",
        f"empty keys {bare.keys()}, single drained to empty",
        quiet and solo and bare.invariant(),
    )


def _the_storm_lands() -> Story:
    storm = run_storm(seed=29)
    return Story(
        "a seeded storm ends where the sort says",
        f"{storm.checks} checks, {storm.breaks} breaks, degree {storm.max_degree}"
        f" under {storm.bound}",
        storm.seated and storm.exact and storm.breaks == 0,
    )


def stories() -> list[Story]:
    """The six stories, told against the live modules right now."""
    return [
        _forest_orders(),
        _a_key_drops(),
        _the_cascade_runs(),
        _debts_stay_paid(),
        _the_edges_answer(),
        _the_storm_lands(),
    ]
