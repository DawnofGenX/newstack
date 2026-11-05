"""Half-open integer intervals: ``[start, end)``.

Every operation here returns *normalised* output: sorted, non-overlapping, and free of
empty intervals. Half-open bounds are what make ``[0, 1)`` and ``[1, 2)`` touch without
overlapping, so they merge into one run and ``coverage`` counts each point exactly once.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

Pair = "Interval | tuple[int, int]"


@dataclass(frozen=True, order=True)
class Interval:
    """One half-open run of integers: ``start`` is inside, ``end`` is not."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(f"interval {self.start}..{self.end} ends before it starts")

    @property
    def empty(self) -> bool:
        """An interval that contains no point at all."""
        return self.end == self.start

    @property
    def length(self) -> int:
        """How many points the interval holds."""
        return self.end - self.start

    def contains(self, point: int) -> bool:
        """Half-open membership: the end is NOT included."""
        return self.start <= point < self.end

    def overlaps(self, other: Interval) -> bool:
        """True when the two intervals share at least one point."""
        return self.start < other.end and other.start < self.end

    def touches(self, other: Interval) -> bool:
        """True when the two intervals are adjacent or overlap, so they can merge."""
        return self.start <= other.end and other.start <= self.end


def _coerce(item: Interval | tuple[int, int]) -> Interval:
    if isinstance(item, Interval):
        return item
    start, end = item
    return Interval(int(start), int(end))


def normalize(items: Iterable[Pair]) -> list[Interval]:
    """Sort, merge everything that touches, and drop empty intervals."""
    ordered = sorted(_coerce(item) for item in items if not _coerce(item).empty)
    merged: list[Interval] = []
    for item in ordered:
        if merged and merged[-1].touches(item):
            last = merged[-1]
            merged[-1] = Interval(last.start, max(last.end, item.end))
        else:
            merged.append(item)
    return merged


def coverage(items: Iterable[Pair]) -> int:
    """How many distinct points the union of the intervals covers."""
    return sum(item.length for item in normalize(items))


def intersect(left: Iterable[Pair], right: Iterable[Pair]) -> list[Interval]:
    """The points both sides cover, as normalised intervals."""
    first, second = normalize(left), normalize(right)
    out: list[Interval] = []
    i = j = 0
    while i < len(first) and j < len(second):
        head = max(first[i].start, second[j].start)
        tail = min(first[i].end, second[j].end)
        if head < tail:
            out.append(Interval(head, tail))
        if first[i].end <= second[j].end:
            i += 1
        else:
            j += 1
    return out


def subtract(left: Iterable[Pair], right: Iterable[Pair]) -> list[Interval]:
    """The points ``left`` covers and ``right`` does not."""
    out: list[Interval] = []
    for piece in normalize(left):
        cursor = piece.start
        for cut in normalize(right):
            if cut.end <= cursor or cut.start >= piece.end:
                continue
            if cut.start > cursor:
                out.append(Interval(cursor, cut.start))
            cursor = max(cursor, cut.end)
            if cursor >= piece.end:
                break
        if cursor < piece.end:
            out.append(Interval(cursor, piece.end))
    return out


def points_to_intervals(points: Iterable[int]) -> list[Interval]:
    """The oracle: turn a set of integers into the intervals that describe it.

    Deliberately the dumbest possible implementation - it exists so the property
    tests have something to compare the clever code against.
    """
    ordered = sorted(set(points))
    if not ordered:
        return []
    runs: list[Interval] = []
    start = previous = ordered[0]
    for point in ordered[1:]:
        if point == previous + 1:
            previous = point
            continue
        runs.append(Interval(start, previous + 1))
        start = previous = point
    runs.append(Interval(start, previous + 1))
    return runs


def expand(items: Iterable[Pair]) -> Iterator[int]:
    """Every point the union covers, in order. Only for small inputs."""
    for item in normalize(items):
        yield from range(item.start, item.end)
