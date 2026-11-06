"""Edit distance, and the two flavours of it this tool is willing to name.

`levenshtein` counts the insertions, deletions and substitutions that turn one
string into the other. With `transpositions=True` it also counts an adjacent
swap as one edit; that variant is optimal string alignment (OSA), and it is
*not* the same function as Damerau-Levenshtein, and it is *not* a metric.

The difference matters more than it looks. A Burkhard-Keller tree prunes by
the triangle inequality, so it needs a metric. OSA can violate it, which is why
`tree.BKTree` falls back to a full scan when transpositions are on instead of
quietly returning the wrong answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["DistanceError", "Measurement", "levenshtein", "osa", "triangle_violation"]


class DistanceError(ValueError):
    """A distance was asked for with an argument it cannot honour."""


@dataclass
class Measurement:
    """A distance and what it cost to compute it."""

    distance: int
    cells: int = 0
    rows: int = 0
    bounded: bool = False
    stopped_early: bool = False

    def line(self) -> str:
        bound = "no limit" if not self.bounded else "bounded"
        early = ", stopped early" if self.stopped_early else ", every row"
        return (
            f"distance   {self.distance}   "
            f"({self.cells} cell(s), {self.rows} row(s), {bound}{early})"
        )


def _measure(a: str, b: str, *, limit: int | None, transpositions: bool) -> Measurement:
    if limit is not None and limit < 0:
        raise DistanceError("a limit below zero cannot be met by any pair of strings")
    if a == b:
        return Measurement(distance=0, cells=0, rows=0, bounded=limit is not None)
    if limit is not None and abs(len(a) - len(b)) > limit:
        return Measurement(distance=limit + 1, cells=0, rows=0, bounded=True, stopped_early=True)
    if not a:
        return Measurement(len(b), cells=0, rows=0, bounded=limit is not None)
    if not b:
        return Measurement(len(a), cells=0, rows=0, bounded=limit is not None)

    width = len(b)
    previous = list(range(width + 1))
    before_previous: list[int] | None = None
    cells = 0
    rows = 0
    for i in range(1, len(a) + 1):
        current = [i] + [0] * width
        left = a[i - 1]
        for j in range(1, width + 1):
            cost = 0 if left == b[j - 1] else 1
            best = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            if (
                transpositions
                and before_previous is not None
                and i > 1
                and j > 1
                and left == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                best = min(best, before_previous[j - 2] + 1)
            current[j] = best
        cells += width
        rows += 1
        if limit is not None and min(current) > limit:
            return Measurement(
                distance=limit + 1,
                cells=cells,
                rows=rows,
                bounded=True,
                stopped_early=True,
            )
        before_previous, previous = previous, current
    distance = previous[width]
    bounded = limit is not None
    if bounded and distance > limit:
        return Measurement(distance=limit + 1, cells=cells, rows=rows, bounded=True)
    return Measurement(distance=distance, cells=cells, rows=rows, bounded=bounded)


def levenshtein(a: str, b: str, *, limit: int | None = None) -> int:
    """The number of insertions, deletions and substitutions that separate a and b.

    With `limit`, a distance larger than the limit is reported as `limit + 1`,
    which is enough to say "no" without computing how much larger it is.
    """
    return _measure(a, b, limit=limit, transpositions=False).distance


def osa(a: str, b: str, *, limit: int | None = None) -> int:
    """Levenshtein plus adjacent transpositions, counted at most once per pair."""
    return _measure(a, b, limit=limit, transpositions=True).distance


def measurement(
    a: str, b: str, *, limit: int | None = None, transpositions: bool = False
) -> Measurement:
    """The distance and the cells it took, for the demos and the reports."""
    return _measure(a, b, limit=limit, transpositions=transpositions)


@dataclass(frozen=True)
class Violation:
    """Three strings where the triangle inequality fails."""

    left: str
    middle: str
    right: str
    direct: int = 0
    through: int = 0

    def lines(self) -> list[str]:
        return [
            f"direct     d({self.left!r}, {self.right!r}) = {self.direct}",
            f"through    d({self.left!r}, {self.middle!r}) + d({self.middle!r}, {self.right!r})"
            f" = {self.through}",
            f"gap        {self.through} < {self.direct}, so the triangle inequality is false",
        ]


def triangle_violation(words: list[str], *, transpositions: bool = True) -> Violation | None:
    """Find three words where d(a, c) > d(a, b) + d(b, c), if there are any."""
    distance = osa if transpositions else levenshtein
    for left in words:
        for right in words:
            direct = distance(left, right)
            for middle in words:
                through = distance(left, middle) + distance(middle, right)
                if through < direct:
                    return Violation(left, middle, right, direct, through)
    return None


@dataclass
class Pair:
    left: str
    right: str
    distance: int = 0
    with_transpositions: int | None = field(default=None)

    def line(self) -> str:
        tail = "" if self.with_transpositions is None else f"   (osa {self.with_transpositions})"
        return f"{self.left!r} vs {self.right!r}: {self.distance}{tail}"
