"""Six stories about keys, sifts, and what a heap owes its head.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .heap import MinHeap
from .oracle import brute_drain, heap_breaks


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the heap makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    heap = MinHeap(corpus)

    ordered = heap.drain() == brute_drain(corpus)
    first = Story(
        "the drain is the plain sort, exactly",
        f"{len(corpus)} keys, sort-equal={ordered}",
        ordered,
    )

    storm = MinHeap(synthetic(48, seed=9))
    shape = not heap_breaks(storm.array())
    second = Story(
        "the parent rule holds on a full array",
        f"48 keys seated, breaks={len(heap_breaks(storm.array()))}",
        shape,
    )

    ladder = MinHeap(list(range(20, 0, -1)))
    sink = MinHeap(list(range(1, 21)))
    descents = ladder.drain() == list(range(1, 21))
    ascents = sink.drain() == list(range(1, 21))
    third = Story(
        "a sunk key and a risen key rest alike",
        f"descents={descents}, ascents={ascents}",
        descents and ascents,
    )

    kept = MinHeap(MinHeap(corpus[:12]).array())
    heads = [kept.peek()]
    for _ in range(6):
        kept.pop()
        heads.append(kept.peek())
    fourth = Story(
        "the head is the minimum of the bag, always",
        f"heads={heads[:3]}..., rising={heads == sorted(heads)}",
        heads == sorted(heads) and heads[0] == min(corpus[:12]),
    )

    pool = synthetic(30, seed=11)
    refilled = MinHeap(pool)
    drained = refilled.drain() == brute_drain(pool)
    refilled.push(1)
    refilled.pop()
    fifth = Story(
        "an emptied heap takes keys again, no residue",
        f"drained={drained}, refilled-drain={refilled.drain() == [1]}, "
        f"empty={len(refilled) == 0}",
        drained and len(refilled) == 0,
    )

    edges = [
        len(MinHeap()) == 0,
        MinHeap([7]).peek() == 7,
        MinHeap([3, 3, 3]).drain() == [3, 3, 3],
    ]
    sixth = Story(
        "empty, single, and repeated keys answer quietly",
        f"edge probes held={all(edges)}",
        all(edges),
    )
    return [first, second, third, fourth, fifth, sixth]
