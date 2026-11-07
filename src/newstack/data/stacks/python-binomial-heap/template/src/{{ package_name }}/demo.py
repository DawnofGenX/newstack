"""Six stories about forests, carries, and what meld is for.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .heap import BinomialHeap, ranks_of
from .streams import synthetic
from .workload import run_meld, run_workload


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the forest makes, each computed fresh."""
    left = BinomialHeap()
    right = BinomialHeap()
    one = synthetic(38, seed=5)
    two = synthetic(26, seed=6)
    for pair in one:
        left.push(*pair)
    for pair in two:
        right.push(*pair)
    truth = sorted([key for key, _ in one] + [key for key, _ in two])
    left.meld(right)
    answered = list(left.pop_all())
    first = Story(
        "meld unions two heaps; a full drain is the sorted concat",
        f"38 + 26 keys, drain sorted={answered == truth}, right drained={len(right) == 0}",
        answered == truth and not right,
    )

    alone = BinomialHeap()
    for key, value in synthetic(64, seed=9):
        alone.push(key, value)
    second = Story(
        "sixty-four pushes, one tree of rank six and 2^6 keys",
        f"ranks {alone.shape()}, shape={alone.shape() == ranks_of(64)},"
        f" invariant={alone.invariant()}",
        alone.shape() == [6] and alone.invariant(),
    )

    mixed = BinomialHeap()
    stand = True
    for index, (key, value) in enumerate(synthetic(60, seed=8)):
        mixed.push(key, value)
        stand = stand and mixed.shape() == ranks_of(len(mixed))
        if index % 4 == 3 and mixed:
            mixed.pop()
            stand = stand and mixed.shape() == ranks_of(len(mixed))
    third = Story(
        "the forest holds one tree per rank after every op",
        f"60 pushes, ~15 pops, ranks {mixed.shape()} of {len(mixed)} keys, stood={stand}",
        stand and mixed.invariant(),
    )

    storm = run_workload(seed=23)
    fourth = Story(
        "a 160-op storm of pushes, pop-mins, and melds holds shape",
        f"{storm.steps} ops, {storm.checks} checks, {storm.melds} melds,"
        f" breaks {storm.breaks}, answers={storm.sorted_held}",
        storm.sorted_held and storm.breaks == 0 and storm.melds > 0,
    )

    small = BinomialHeap()
    small.push(9, "nine")
    big = BinomialHeap()
    for key in (4, -3, 12):
        big.push(key, None)
    big.meld(small)
    fifth = Story(
        "pop-min of a meld is the min of the union",
        f"meld(-3,4,12) + (9) -> peek {big.peek()[0]!r}, min(-3,4,9,12) is -3",
        big.peek()[0] == -3,
    )

    drain = run_meld(seed=31, left=20, right=11)
    sixth = Story(
        "meld twice, drain once, the concat survives",
        f"{drain.steps} keys, {drain.links} links, sorted={drain.sorted_held},"
        f" shapes={drain.shapes_held}",
        drain.sorted_held and drain.shapes_held and drain.breaks == 0,
    )
    return [first, second, third, fourth, fifth, sixth]


def render_stories() -> str:
    """The stories as a report; the tail line is what smoke tests read."""
    told = stories()
    rows = [f"{index}. {story.title}" for index, story in enumerate(told, start=1)]
    rows += [f"   {story.detail}" for story in told]
    holds = sum(1 for story in told if story.held)
    rows.append(f"{holds} of {len(told)} hold")
    return "\n".join(rows)
