"""Six stories about cells, bits, and the sums a tree owes an answer to.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fenwick import Fenwick, build_cells
from .streams import synthetic
from .workload import run_walks, run_workload


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the tree makes, each computed fresh."""
    storm = run_workload(seed=29)
    first = Story(
        "every prefix equals the running list-sum reference",
        f"{storm.steps} seeded adds and queries, {storm.checks} checks,"
        f" breaks {storm.breaks}, total exact={storm.exact}",
        storm.breaks == 0 and storm.exact,
    )

    census = run_walks(seed=31, size=512)
    second = Story(
        "no walk visits more cells than the bit-length of the size",
        f"512 cells, longest walk {census.longest} of limit {census.limit},"
        f" overruns {census.breaks}",
        census.breaks == 0 and census.longest <= census.limit,
    )

    values = synthetic(200, seed=11)
    folded = build_cells(values)
    cellwise = [0] * (len(values) + 1)
    for index, value in enumerate(values):
        cell = index + 1
        while cell <= len(values):
            cellwise[cell] += value
            cell += cell & -cell
    third = Story(
        "the one-pass fold builds cells identical to one add per value",
        f"{len(values)} values, cells identical={folded == cellwise}",
        folded == cellwise,
    )

    tree = Fenwick(values)
    window = tree.range_sum(9, 150)
    fourth = Story(
        "a range sum is two prefixes and the slice the reference took",
        f"window 9..150 answered {window.answer},"
        f" reference says {sum(values[9:150])}, cells {window.cells}",
        window.answer == sum(values[9:150]),
    )

    edges = Fenwick([]).prefix(0).answer == 0 and Fenwick([41]).prefix(1).answer == 41
    fifth = Story(
        "the empty tree answers zero and the lone cell answers itself",
        f"empty prefix {'0'} and lone prefix {'41'} both honest={edges}",
        edges,
    )

    rebuilt = Fenwick(values)
    for index in range(0, len(values), 7):
        rebuilt.add(index, 3)
    rebuilt.rebuild()
    sixth = Story(
        "a rebuild after an add storm re-folds the very same cells",
        f"200 values, {len(range(0, 200, 7))} adds then a rebuild,"
        f" invariant={rebuilt.invariant()}",
        rebuilt.invariant(),
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
