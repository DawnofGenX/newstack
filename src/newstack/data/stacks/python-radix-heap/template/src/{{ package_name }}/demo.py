"""Six stories about buckets, bits, and what it costs to keep them true.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .heap import BUCKETS, RadixHeap, bucket_of
from .streams import monotone, synthetic
from .workload import run_monotone, run_workload


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the heap makes, each computed fresh."""
    mixed = synthetic(200, seed=5)
    keys = sorted(key for key, _ in mixed)

    quiet = RadixHeap()
    for key, value in mixed:
        quiet.push(key, value)
    answered = list(quiet.pop_all())
    first = Story(
        "pop-min answers sorted, without one comparison",
        f"{len(keys)} shuffled keys drained -> sorted={answered == keys}",
        answered == keys,
    )

    seated = RadixHeap()
    for key, _ in mixed[:64]:
        seated.push(key, None)
    seats = [bucket_of(key, seated.base) for key, _ in mixed[:64]]
    second = Story(
        "every key sits at its bit-length-from-base bucket",
        f"{len(seats)} keys, buckets {min(seats)}..{max(seats)} of {BUCKETS},"
        f" invariant={seated.invariant()}",
        seated.invariant(),
    )

    forward = run_monotone(seed=3, size=96)
    third = Story(
        "a monotone stream never pays a rebuild",
        f"{forward.steps} pushes, {forward.rebuilds} rebuilds, sorted={forward.sorted_held}",
        forward.rebuilds == 0 and forward.breaks == 0 and forward.sorted_held,
    )

    storm = run_workload(seed=23)
    fourth = Story(
        "a mixed storm keeps the invariant after every op",
        f"{storm.steps} ops, {storm.checks} checks, breaks {storm.breaks},"
        f" sorted={storm.sorted_held}",
        storm.sorted_held and storm.breaks == 0,
    )

    back = RadixHeap()
    for key in (5, 9, 14):
        back.push(key, None)
    back.pop()
    before = back.stats()
    back.push(3, None)
    after = back.stats()
    fifth = Story(
        "a backwards push buys exactly one rebuild",
        f"pop 5 then push 3: rebuilds {before['rebuilds']} -> {after['rebuilds']},"
        f" answer still sorted={list(back.pop_all()) == [3, 9, 14]}",
        after["rebuilds"] == before["rebuilds"] + 1 and after["invariant"],
    )

    six = _window_walk()
    return [first, second, third, fourth, fifth, six]


def _quiet(keys: list[int]) -> list[int]:
    heap = RadixHeap()
    for key in keys:
        heap.push(key, None)
    return list(heap.pop_all())


def _window_walk() -> Story:
    stream = monotone(48, seed=9)
    heap = RadixHeap()
    for key, value in stream:
        heap.push(key, value)
    walked = []
    for _ in range(6):
        key, _ = heap.pop()
        walked.append(key)
    base = heap.base
    held = [key for key, _ in heap.entries()]
    honest = all(bucket_of(key, base) >= 1 for key in held) and walked == sorted(walked)
    return Story(
        "the window walks forward and drops nothing behind",
        f"six pops land {walked[:2]}..{walked[-1:]}, base {base},"
        f" survivors ahead of it={honest}",
        honest,
    )


def render_stories() -> str:
    """The stories as a report; the tail line is what smoke tests read."""
    told = stories()
    rows = [f"{index}. {story.title}" for index, story in enumerate(told, start=1)]
    rows += [f"   {story.detail}" for story in told]
    holds = sum(1 for story in told if story.held)
    rows.append(f"{holds} of {len(told)} hold")
    return "\n".join(rows)
