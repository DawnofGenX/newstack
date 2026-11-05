"""Offline checks: no pytest, no hypothesis, no files left behind."""

from __future__ import annotations

from .cli import minimal_counterexample, naive_coverage
from .intervals import (
    Interval,
    coverage,
    expand,
    intersect,
    normalize,
    points_to_intervals,
    subtract,
)


def run() -> int:
    """Return 0 when every check passed."""
    checks = 0
    failures: list[str] = []

    def check(condition: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(what)

    unit = Interval(3, 4)
    check(unit.length == 1, "a unit interval covers one point")
    check(unit.contains(3) and not unit.contains(4), "the end bound is not included")
    check(unit.empty is False, "a unit interval is not empty")
    check(Interval(3, 3).empty is True, "start equal to end is empty")

    try:
        Interval(5, 2)
    except ValueError:
        check(True, "a backwards interval is rejected")
    else:
        check(False, "a backwards interval is rejected")

    check(normalize([]) == [], "nothing normalises to nothing")
    check(normalize([(2, 4), (0, 2)]) == [Interval(0, 4)], "touching intervals merge")
    check(normalize([(0, 4), (2, 6)]) == [Interval(0, 6)], "overlapping intervals merge")
    check(normalize([(0, 1), (3, 4)]) == [Interval(0, 1), Interval(3, 4)], "gaps survive")
    check(normalize([(1, 1), (0, 2)]) == [Interval(0, 2)], "empty intervals are dropped")
    check(normalize([(0, 2), (0, 2)]) == [Interval(0, 2)], "duplicates collapse")

    check(coverage([(0, 2), (1, 3)]) == 3, "overlap is counted once")
    check(coverage([(0, 1), (1, 2)]) == 2, "touching intervals cover two points")
    check(naive_coverage([Interval(0, 2), Interval(1, 3)]) == 4, "the naive sum double counts")

    check(intersect([(0, 4)], [(2, 6)]) == [Interval(2, 4)], "intersection of two overlaps")
    check(intersect([(0, 1)], [(1, 2)]) == [], "touching intervals do not intersect")
    check(intersect([(0, 2), (4, 6)], [(1, 5)]) == [Interval(1, 2), Interval(4, 5)], "two pieces")

    check(subtract([(0, 6)], [(2, 3)]) == [Interval(0, 2), Interval(3, 6)], "subtract a hole")
    check(subtract([(0, 2)], [(0, 2)]) == [], "subtract everything")
    check(subtract([(0, 2)], [(5, 6)]) == [Interval(0, 2)], "subtracting nothing changes nothing")
    check(subtract([(0, 4)], [(1, 9)]) == [Interval(0, 1)], "subtract a longer interval")

    check(points_to_intervals([]) == [], "no points is no interval")
    check(points_to_intervals([3]) == [Interval(3, 4)], "one point is one unit interval")
    check(
        points_to_intervals([4, 1, 2, 3, 7]) == [Interval(1, 5), Interval(7, 8)],
        "unordered points form runs",
    )
    check(list(expand([(0, 2), (1, 3)])) == [0, 1, 2], "expand yields each point once")

    items, naive, real = minimal_counterexample()
    check(items == [Interval(0, 1), Interval(0, 1)], "the smallest counterexample is two unit runs")
    check((naive, real) == (2, 1), "the naive sum reports two points where there is one")

    if failures:
        for failure in failures:
            print(f"selftest: FAILED {failure}")
        print(f"selftest: {len(failures)} of {checks} checks failed")
        return 1
    print(f"selftest: {checks} checks passed")
    return 0
