"""The invariants this ladder promises, run against the real modules.

Every claim here is the reason the ladder can be trusted: every window
must answer exactly as the matching slice sums, a rebuild from the leaf
row must equal the build it came from, and no query may visit more
than twice the bit-length of the array. Runnable in a fresh checkout:
`{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .array import (
    DEFAULT_SEED,
    ArrayValueError,
    describe,
    ensure_value,
    load_values,
    synthetic,
    write_values,
)
from .tree import NEUTRAL, SegmentError, SegmentTree, addition, minimum
from .workload import STEPS, WorkloadError, run_bound, run_workload

FIXTURE = "a pull-up re-folds the path"
VALUES = [3, -1, 4, 1, -5, 9, 2, 6, -5, 3, 5, -2]


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
            f"{claim} ({found!r})"
            if found == expected
            else f"{claim}: {found!r} != {expected!r}",
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
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self.lines, "", tail))


def _windows(report: Report) -> None:
    report.section("every window answers as its slice sums")
    tree = SegmentTree(VALUES)
    worst = 0
    exact = True
    for low in range(len(VALUES) + 1):
        for high in range(low, len(VALUES) + 1):
            exact = exact and tree.query(low, high) == sum(VALUES[low:high])
            worst = max(worst, tree.visits)
    report.ok("every window of the twelve is exact", exact)
    report.ok(
        f"visits stay under twice the bit-length ({worst} of {2 * len(VALUES).bit_length()})",
        worst <= 2 * len(VALUES).bit_length(),
    )
    report.equal("the empty window answers the identity", tree.query(4, 4), NEUTRAL)
    report.equal("the full window answers the total", tree.query(0, 12), sum(VALUES))


def _edits(report: Report) -> None:
    report.section("an edit re-folds only the path it touches")
    tree = SegmentTree(VALUES)
    tree.set(4, 40)
    report.equal("set lands on the leaf", tree.leaves()[4], 40)
    report.equal("the root followed", tree.root, sum(VALUES) + 45)
    report.ok("the ladder still folds itself", tree.invariant())
    tree.add(9, -10)
    report.equal("add slides the leaf", tree.leaves()[9], -7)
    report.equal(
        "the full answer followed",
        tree.query(0, 12),
        sum(VALUES) + 45 - 10,
    )
    report.refuses("an index past the end is refused", lambda: tree.set(12, 0), SegmentError)
    report.refuses("a negative index is refused", lambda: tree.add(-1, 1), SegmentError)


def _rebuild(report: Report) -> None:
    report.section("a rebuild from the leaf row equals its build")
    tree = SegmentTree(VALUES)
    tree.set(0, -99)
    tree.add(11, 7)
    rebuilt = SegmentTree(tree.leaves(), tree.combine)
    report.equal("the fingerprints match", rebuilt.fingerprint(), tree.fingerprint())
    report.ok("a rebuilt ladder folds itself", rebuilt.invariant())
    report.equal("a rebuilt window answers the same",
                 rebuilt.query(3, 9), tree.query(3, 9))


def _seam(report: Report) -> None:
    report.section("the combine is the seam, not the answer")
    floor = SegmentTree(VALUES, minimum)
    report.equal("the same walk answers a floor", floor.query(2, 8), min(VALUES[2:8]))
    report.equal("the full walk answers the minimum", floor.query(0, 12), min(VALUES))
    report.equal("sum still sums under the fold", addition(3, 4), 7)
    report.equal("min still mins under the fold", minimum(3, 4), 3)
    odd = SegmentTree(VALUES, lambda a, b: a if a >= b else b)
    report.ok("a stranger fold keeps the invariant", odd.invariant())
    walked = 0
    exact = True
    for low in range(13):
        for high in range(low + 1, 13):
            answer = odd.query(low, high)
            walked = max(walked, odd.visits)
            exact = exact and answer == max(VALUES[low:high])
    report.ok("the stranger fold answers its own truth", exact)
    report.ok("even under max the visits stay bounded",
              walked <= 2 * len(VALUES).bit_length())


def _storm(report: Report) -> None:
    report.section("the storm, replayed against the slice truth")
    storm = run_workload(seed=13)
    report.equal("the storm ran its steps", storm.steps, STEPS)
    report.equal("the storm broke nothing", storm.breaks, 0)
    report.ok("every storm answer was exact", storm.exact)
    report.ok("the storm rebuilt what it was", storm.rebuild_equal)
    report.ok("the storm visited inside its bound", storm.max_visits <= storm.bound)
    bound = run_bound(size=48, seed=11)
    report.ok("every window of 48 answered exact", bound.exact)
    report.ok("no visit missed the bound", bound.max_visits <= bound.bound)
    report.refuses(
        "a storm outside its bounds is refused",
        lambda: run_workload(steps=0),
        WorkloadError,
    )


def _values(report: Report) -> None:
    report.section("the ladder folds whole numbers as they stand")
    report.equal("the value comes back itself", ensure_value(7), 7)
    report.equal("a value renders as itself", describe(-4), "-4")
    report.refuses("a list has no seat", lambda: ensure_value([1]), ArrayValueError)
    report.refuses("a flag is no value", lambda: ensure_value(True), ArrayValueError)
    grown = synthetic(40, seed=3)
    report.equal("the generator is deterministic", grown, synthetic(40, seed=3))
    report.equal("the generator grew a ladder's worth", len(grown), 40)
    report.refuses("an array of zero is no array", lambda: synthetic(0), ArrayValueError)
    report.equal("the default seed is the record", DEFAULT_SEED, 7)


def _streams(report: Report) -> None:
    report.section("the array in and the file out")
    with TemporaryDirectory() as room:
        path = f"{room}/values.txt"
        write_values(VALUES, path)
        report.equal("a written array reads back", load_values(path), VALUES)
        report.refuses(
            "a missing array is named", lambda: load_values(f"{room}/missing.txt"),
            ArrayValueError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1 2\n")
        report.refuses("an array of noise is refused",
                       lambda: load_values(noise), ArrayValueError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import tree as tree_module

    report.ok(
        "the marker the detector looks for is in the tree module",
        FIXTURE in " ".join((tree_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _windows(report)
    _edits(report)
    _rebuild(report)
    _seam(report)
    _storm(report)
    _values(report)
    _streams(report)
    _stories(report)
    return report
