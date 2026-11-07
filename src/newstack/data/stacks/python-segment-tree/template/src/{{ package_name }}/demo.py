"""Six stories about ladders, windows, and what it costs to keep them true.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tree import SegmentTree, minimum
from .workload import run_bound, run_workload

VALUES = [3, -1, 4, 1, -5, 9, 2, 6, -5, 3, 5, -2]


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the ladder makes, each computed fresh."""
    storm = run_workload(seed=23)
    first = Story(
        "every window answers exactly as its slice sums",
        f"{storm.checks} checks, {storm.breaks} breaks, exact={storm.exact}",
        storm.exact and storm.breaks == 0,
    )

    tree = SegmentTree(VALUES)
    tree.set(4, 40)
    tree.add(9, -10)
    second = Story(
        "a point edit re-folds only the path it touches",
        f"set 4 -> 40, add 9 by -10: answer {tree.query(0, 12)}"
        " == edited slice",
        tree.query(0, 12)
        == sum([3, -1, 4, 1, 40, 9, 2, 6, -5, -7, 5, -2])
        and tree.invariant(),
    )

    bound = run_bound(size=96)
    third = Story(
        "a query visits at most twice the bit-length of the array",
        f"{bound.checks} windows, max visits {bound.max_visits} of bound {bound.bound}",
        bound.max_visits <= bound.bound and bound.exact,
    )

    edges = SegmentTree(VALUES)
    fourth = Story(
        "an empty window answers zero, a full one answers the total",
        f"empty 0 (want 0), full {edges.query(0, 12)} (want {sum(VALUES)})",
        edges.query(0, 0) == 0 and edges.query(0, 12) == sum(VALUES),
    )

    rebuilt = SegmentTree(edges.leaves(), edges.combine)
    fifth = Story(
        "a rebuild from the leaf row equals the build it came from",
        f"fingerprints equal={rebuilt.fingerprint() == edges.fingerprint()}"
        f", leaves {len(rebuilt.leaves())}",
        rebuilt.fingerprint() == edges.fingerprint(),
    )

    floor = SegmentTree(VALUES, minimum)
    sixth = Story(
        "the combine is the seam: the same walk answers a floor",
        f"minimum tree over 12 values: [2, 8) = {floor.query(2, 8)}"
        f" (want {min(VALUES[2:8])})",
        floor.query(2, 8) == min(VALUES[2:8]) and floor.query(0, 12) == min(VALUES),
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
