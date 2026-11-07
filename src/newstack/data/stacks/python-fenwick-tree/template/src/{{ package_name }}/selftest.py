"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the cells can be trusted: every prefix
must equal the running list-sum reference on seeded add/sum workloads,
no walk may visit more cells than the bit-length of the size, the
one-pass fold must build cells identical to one add per value, and the
empty and lone trees must answer honestly. Runnable in a fresh
checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .fenwick import Fenwick, FenwickError, build_cells, step_of
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_values,
    rising,
    synthetic,
    write_values,
)
from .values import ValueRejection, describe, ensure_value, step_size
from .workload import WorkloadError, run_walks, run_workload

FIXTURE = "the lowest set bit"
VALUES = [-5, 0, 3, 11, 7, -2, 18, 26, 9, 40, 14, 63, 5, 31, 22, 57]


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


def _steps(report: Report) -> None:
    report.section("the step is the lowest set bit")
    report.equal("one climbs by one", step_of(1), 1)
    report.equal("six climbs by two", step_of(6), 2)
    report.equal("twelve climbs by four", step_of(12), 4)
    report.equal("seven climbs by one", step_of(7), 1)
    report.equal("the values module agrees", step_size(12), step_of(12))
    report.refuses("cell zero has no step", lambda: step_of(0), FenwickError)
    report.refuses("a list is no value", lambda: ensure_value([1]), ValueRejection)
    report.refuses("a flag is no value", lambda: ensure_value(True), ValueRejection)
    report.equal("a value renders as itself", describe(42), "42")


def _edges(report: Report) -> None:
    report.section("empty and lone answer honestly")
    report.equal("the empty tree answers zero", Fenwick([]).prefix(0).answer, 0)
    report.equal("the lone cell answers itself", Fenwick([41]).prefix(1).answer, 41)
    report.equal("the lone prefix of zero is zero", Fenwick([41]).prefix(0).answer, 0)
    report.ok("the empty tree is honest", Fenwick([]).invariant())
    report.equal("the empty tree is no size", len(Fenwick([])), 0)
    report.refuses(
        "a count past the lone tree is refused",
        lambda: Fenwick([41]).prefix(2),
        FenwickError,
    )
    report.refuses("index one sits outside the lone tree",
                   lambda: Fenwick([41]).add(1, 3), FenwickError)


def _prefix(report: Report) -> None:
    report.section("every prefix equals the running list-sum reference")
    tree = Fenwick(VALUES)
    for count in range(len(VALUES) + 1):
        report.equal(
            f"prefix {count} matches the reference",
            tree.prefix(count).answer,
            sum(VALUES[:count]),
        )
    report.equal("the total is the whole corpus", tree.prefix(16).answer, sum(VALUES))
    report.ok("the built tree is honest", tree.invariant())


def _climb(report: Report) -> None:
    report.section("an add shifts the mirror and the cells together")
    tree = Fenwick(VALUES)
    tree.add(2, 7)
    report.equal("the mirror moved", tree.value(2), 10)
    report.equal("the prefix moved with it", tree.prefix(5).answer, sum(VALUES[:5]) + 7)
    report.equal("the far prefix moved too", tree.prefix(16).answer, sum(VALUES) + 7)
    report.ok("the cells stayed honest", tree.invariant())
    walk = tree.add(0, 1)
    report.ok("the climb counted its cells", walk.cells >= 1)
    report.ok("the climb stayed under the limit", walk.cells <= tree.limit)
    report.refuses(
        "a delta that is no number is refused",
        lambda: tree.add(0, "seven"),  # type: ignore[arg-type]
        ValueRejection,
    )


def _walks(report: Report) -> None:
    report.section("no walk visits more cells than the bit-length")
    census = run_walks(seed=31, size=512)
    report.equal("the census broke no bound", census.breaks, 0)
    report.ok("the longest walk fits the limit", census.longest <= census.limit)
    equal = Fenwick(synthetic(1024, seed=5))
    report.equal("a thousand cells still answer in ten", equal.prefix(1024).cells, 1)
    report.ok("the limit is the bit-length", equal.limit == (1024).bit_length())


def _fold(report: Report) -> None:
    report.section("the one-pass fold equals one add per value")
    for size, seed in ((0, 1), (1, 2), (17, 3), (96, 4)):
        values = synthetic(max(size, 1), seed=seed)[:size]
        folded = build_cells(values)
        cellwise = [0] * (size + 1)
        for index, value in enumerate(values):
            cell = index + 1
            while cell <= size:
                cellwise[cell] += value
                cell += cell & -cell
        report.equal(f"{size} values fold the same", folded, cellwise)
    tree = Fenwick(VALUES)
    for index in range(len(VALUES)):
        tree.add(index, index * 3 - 20)
    before = tree.cells()
    tree.rebuild()
    report.equal("a rebuild re-folds identical cells", tree.cells(), before)
    report.ok("the rebuilt tree is honest", tree.invariant())


def _window(report: Report) -> None:
    report.section("a range is two prefixes and the slice it names")
    tree = Fenwick(VALUES)
    report.equal("the middle window matches the slice",
                 tree.range_sum(3, 11).answer, sum(VALUES[3:11]))
    report.equal("the whole window is the total",
                 tree.range_sum(0, 16).answer, sum(VALUES))
    report.equal("an empty window is zero", tree.range_sum(5, 5).answer, 0)
    report.refuses("an inverted window is refused",
                   lambda: tree.range_sum(9, 2), FenwickError)
    report.refuses("a window past the tree is refused",
                   lambda: tree.range_sum(0, 17), FenwickError)
    tree.add(4, -30)
    report.equal("the window tracked the add",
                 tree.range_sum(3, 11).answer, sum(VALUES[3:11]) - 30)


def _streams(report: Report) -> None:
    report.section("the values in and the snapshot out")
    values = synthetic(60, seed=5)
    report.equal("the generator is deterministic", values, synthetic(60, seed=5))
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), StreamError)
    climb = rising(32, seed=4)
    report.equal("the rising stream rises", climb, sorted(climb))
    frozen = Snapshot(values, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its values", thawed.values, values)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        StreamError,
    )
    with TemporaryDirectory() as room:
        path = f"{room}/values.txt"
        write_values(values, path)
        report.equal("a written list reads back", load_values(path), values)
        report.refuses(
            "a missing list is named", lambda: load_values(f"{room}/missing.txt"),
            StreamError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nseven\n")
        report.refuses("a list of noise is refused", lambda: load_values(noise),
                       StreamError)


def _storms(report: Report) -> None:
    report.section("the storms, replayed against the list-sum truth")
    storm = run_workload(seed=13)
    report.equal("the storm ran its steps", storm.steps, 160)
    report.equal("the storm broke no invariant", storm.breaks, 0)
    report.ok("the storm answered exactly", storm.exact)
    report.ok("the storm checked more than it stepped", storm.checks > storm.steps)
    report.ok("no walk outgrew the limit", storm.longest <= storm.limit)
    report.refuses(
        "a storm outside its bounds is refused",
        lambda: run_workload(steps=0),
        WorkloadError,
    )


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import fenwick as fenwick_module

    report.ok(
        "the marker the detector looks for is in the tree module",
        FIXTURE in " ".join((fenwick_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _steps(report)
    _edges(report)
    _prefix(report)
    _climb(report)
    _walks(report)
    _fold(report)
    _window(report)
    _streams(report)
    _storms(report)
    _stories(report)
    return report
