"""The invariants this forest promises, run against the real modules.

Every claim here is the reason the answers are trustworthy: the partition
must equal a dict-of-parents reference after a seeded workload, depth
must stay logarithmic before compression is asked for, compression must
never move an element to a different component, union must be idempotent,
and a render from (element, root) pairs must rebuild the same partition.
Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .forest import (
    UnionFind,
    UnionFindError,
)
from .pairs import synthetic

MARKER = "a merge rewrites nothing"


class Reference:
    """The dict-of-parents model the forest is checked against."""

    def __init__(self, elements: list[int]) -> None:
        self.parent = {element: element for element in elements}

    def union(self, first: int, second: int) -> None:
        left, right = self.find(first), self.find(second)
        if left != right:
            self.parent[right] = left

    def find(self, element: int) -> int:
        while self.parent[element] != element:
            element = self.parent[element]
        return element

    def partition(self) -> list[frozenset[int]]:
        groups: dict[int, set[int]] = {}
        for element in self.parent:
            groups.setdefault(self.find(element), set()).add(element)
        return sorted((frozenset(members) for members in groups.values()), key=min)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})" if found == expected else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, call: object, error: type[Exception]) -> None:
        try:
            call()  # type: ignore[operator]
        except error as seen:
            self.ok(f"{claim} ({seen})", True)
        except Exception as seen:
            self.ok(f"{claim}: raised {type(seen).__name__}, not {error.__name__}", False)
        else:
            self.ok(f"{claim}: nothing raised", False)

    def render(self) -> str:
        body = "\n".join(self.lines)
        return f"{body}\n\nselftest: {self.checks} checks passed, {self.failed} failed"


def _partition(forest: UnionFind) -> list[frozenset[int]]:
    return sorted((frozenset(group) for group in forest.components()), key=min)


def _opened(report: Report) -> None:
    report.section("an element opens alone and stays where it opened")
    forest = UnionFind()
    report.ok("the first add opens", forest.add(7))
    report.ok("the second add is already there", not forest.add(7))
    report.equal("a lone element names itself", forest.find(7), 7)
    report.equal("one element is one component", forest.count, 1)
    report.equal("and one element in the forest", len(forest), 1)
    report.refuses("an outsider is named", lambda: forest.find(8), UnionFindError)
    report.refuses("a bool is not an element", lambda: forest.add(True), UnionFindError)


def _reference(report: Report) -> None:
    report.section("the partition equals a dict-of-parents reference")
    for seed in (3, 19, 44):
        pairs = synthetic(120, seed=seed, low=0, high=80)
        elements = sorted({value for pair in pairs for value in pair})
        forest = UnionFind(elements)
        model = Reference(elements)
        for first, second in pairs:
            forest.union(first, second)
            model.union(first, second)
        landed = _partition(forest) == model.partition()
        report.equal(f"seed {seed} lands on the reference partition", landed, True)


def _depth(report: Report) -> None:
    report.section("union by size keeps depth logarithmic before compression")
    for size in (64, 256, 1024):
        forest = UnionFind(range(size))
        left = 0
        for right in range(1, size):
            forest.union(left, right)
        budget = math.ceil(math.log2(size)) + 1
        depth = forest.shape().max_depth
        report.ok(f"a chain of {size} rests under depth {budget} ({depth})", depth <= budget)


def _compression(report: Report) -> None:
    report.section("compression never moves an element to another component")
    for seed in (5, 21):
        pairs = synthetic(200, seed=seed, low=0, high=120)
        elements = sorted({value for pair in pairs for value in pair})
        forest = UnionFind(elements)
        for first, second in pairs:
            forest.union(first, second)
        before = _partition(forest)
        names = {element: forest.find(element) for element in elements}
        after = _partition(forest)
        report.equal(f"seed {seed}: compression kept the partition", before, after)
        report.equal(
            f"seed {seed}: every compressed walk names the same root",
            {element: forest.root_of(element) for element in elements},
            names,
        )
        report.ok(
            f"seed {seed}: compression actually rewrote",
            forest.shape().roots_rewritten > 0,
        )


def _idempotence(report: Report) -> None:
    report.section("union is idempotent")
    forest = UnionFind(range(40))
    report.ok("the first merge lands", forest.union(3, 17))
    before = _partition(forest)
    for _ in range(10):
        report.ok("a repeat merge changes nothing", not forest.union(3, 17))
    report.equal("ten repeats leave one partition", _partition(forest), before)
    report.equal("and no extra rewrites", forest.shape().roots_rewritten, 0)


def _render(report: Report) -> None:
    report.section("a render from (element, root) pairs rebuilds the partition")
    for seed in (8, 31):
        pairs = synthetic(90, seed=seed, low=0, high=60)
        elements = sorted({value for pair in pairs for value in pair})
        forest = UnionFind(elements)
        for first, second in pairs:
            forest.union(first, second)
        fresh = UnionFind.from_snapshot(dict(forest.snapshot()))
        same = _partition(fresh) == _partition(forest)
        report.equal(f"seed {seed}: the render partitions identically", same, True)
        report.equal("and counts the same components", fresh.count, forest.count)
    report.refuses(
        "a name that is not an element is refused",
        lambda: UnionFind.from_snapshot([(1, 2)]),
        UnionFindError,
    )
    report.refuses(
        "two names for one element are refused",
        lambda: UnionFind.from_snapshot([(1, 1), (2, 2), (1, 2)]),
        UnionFindError,
    )


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import forest as forest_module

    joined = " ".join((forest_module.__doc__ or "").split())
    report.ok("the marker sits in the forest docstring", MARKER in joined)


def run() -> Report:
    report = Report()
    _opened(report)
    _reference(report)
    _depth(report)
    _compression(report)
    _idempotence(report)
    _render(report)
    _marker(report)
    return report
