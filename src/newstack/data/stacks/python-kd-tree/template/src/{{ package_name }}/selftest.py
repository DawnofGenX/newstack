"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the splits can be trusted: membership
must equal a set's answer on seeded corpora, every rectangle answer
must equal the brute-force filter, the nearest answer must equal the
brute-force argmin with the tie on the smallest point, and a rebuild
from the in-order walk must answer identically. Runnable in a fresh
checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_points,
    synthetic,
    write_points,
)
from .points import PointError, ensure_point, ensure_rect
from .scan import scan_has, scan_nearest, scan_range
from .tree import KDTree, distance
from .workload import WorkloadError, rebuild_matches, run_storm

FIXTURE = "a split divides, never the answer"
POINTS = [(0, 0), (5, 5), (5, -5), (-5, 5), (-5, -5), (9, 4), (10, -10)]


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


def _gate(report: Report) -> None:
    report.section("the gate keeps half-points out of the plane")
    report.equal("a pair comes back itself", ensure_point((3, -4)), (3, -4))
    report.equal("the edge sits on the gate", ensure_rect((-9, -9, 9, 9)), (-9, -9, 9, 9))
    report.refuses("a lone integer is no point", lambda: ensure_point(7), PointError)
    report.refuses("a float is no coordinate", lambda: ensure_point((1.5, 2)), PointError)
    report.refuses("a bool is no coordinate", lambda: ensure_point((True, 2)), PointError)
    report.refuses("past the edge is no point",
                   lambda: ensure_point((10**9 + 1, 0)), PointError)
    report.refuses("min past max is no rectangle",
                   lambda: ensure_rect((5, 0, 0, 5)), PointError)


def _membership(report: Report) -> None:
    report.section("membership answers what a set answers")
    corpus = synthetic(120, seed=17, span=40)
    tree = KDTree(corpus)
    stored = set(corpus)
    report.equal("the count is the set's size", tree.count(), len(stored))
    for probe in [*corpus[::11], (0, 0), (10**9, 10**9), corpus[0]]:
        report.ok(f"{probe!r} answers like the set",
                  tree.has(probe) is scan_has(corpus, probe))
    report.equal("the walk holds every point once",
                 sorted(tree.walk()), sorted(stored))


def _rectangles(report: Report) -> None:
    report.section("every rectangle answer is the brute-force filter")
    corpus = synthetic(150, seed=23, span=45)
    tree = KDTree(corpus)
    boxes = [
        (-45, -45, 45, 45),
        (0, 0, 10, 10),
        (5, 5, 5, 5),
        (-20, 30, -10, 40),
        (100, 100, 200, 200),
        (min(corpus[7][0], corpus[9][0]), min(corpus[7][1], corpus[9][1]),
         max(corpus[7][0], corpus[9][0]), max(corpus[7][1], corpus[9][1])),
    ]
    for box in boxes:
        report.equal(f"box {box!r} filters the scan",
                     tree.range(box), scan_range(corpus, box))
    whole = tree.range((-10**9, -10**9, 10**9, 10**9))
    report.equal("the whole plane lists every point", whole, sorted(set(corpus)))
    report.equal("the whole plane invents nothing", len(whole), len(set(corpus)))


def _nearest(report: Report) -> None:
    report.section("the nearest answer is the brute-force argmin")
    corpus = synthetic(140, seed=29, span=40)
    tree = KDTree(corpus)
    queries = [(0, 0), corpus[3], (-1, -1), (39, 39), (10**9, -10**9)]
    queries += [corpus[seed % len(corpus)] for seed in (7, 41, 1009)]
    for probe in queries:
        report.equal(f"{probe!r} finds the argmin",
                     tree.nearest(probe), scan_nearest(corpus, probe))
    tied = KDTree([(0, 2), (2, 0), (-2, 0), (0, -2)])
    report.equal("the tie goes to the smallest point",
                 tied.nearest((0, 0)), (-2, 0))
    report.equal("the tie answer is the scan's answer",
                 tied.nearest((0, 0)), scan_nearest([(0, 2), (2, 0), (-2, 0), (0, -2)], (0, 0)))
    report.equal("distance ranks what the scan ranks",
                 distance((3, 4), (0, 0)), 25)


def _rebuild(report: Report) -> None:
    report.section("a rebuild from the walk answers identically")
    corpus = synthetic(80, seed=55, span=35)
    report.ok("two trees, one corpus, identical answers",
              rebuild_matches(corpus))
    first = KDTree(corpus)
    second = KDTree(list(reversed(sorted(corpus))))
    report.equal("insertion order is not an answer",
                 sorted(first.walk()), sorted(second.walk()))
    rebuilt = KDTree(first.walk())
    report.equal("the walk rebuilds the same tree size", rebuilt.count(), first.count())
    report.equal("the rebuilt walk equals the first",
                 sorted(rebuilt.walk()), sorted(first.walk()))
    for probe in [corpus[5], (0, 0)]:
        report.equal("the rebuild answers the same",
                     rebuilt.nearest(probe), first.nearest(probe))


def _corpora(report: Report) -> None:
    report.section("the point list in, the snapshot out")
    corpus = synthetic(60, seed=5, span=30)
    report.equal("the generator is deterministic",
                 corpus, synthetic(60, seed=5, span=30))
    report.ok("the points are distinct", len(set(corpus)) == 60)
    report.refuses("a corpus of zero is no corpus",
                   lambda: synthetic(0), CorpusError)
    report.refuses("a span too small is refused",
                   lambda: synthetic(10, span=2), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its points", list(thawed.points), corpus)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses("half a snapshot is no snapshot",
                   lambda: Snapshot.loads('{"seed": 1}'), CorpusError)
    with TemporaryDirectory() as room:
        path = f"{room}/points.txt"
        write_points(corpus, path)
        report.equal("a written list reads back", load_points(path), corpus)
        report.refuses("a missing list is named",
                       lambda: load_points(f"{room}/missing.txt"), CorpusError)
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1,2,3\n")
        report.refuses("a noisy list is refused",
                       lambda: load_points(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every op")
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 160)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.ok(f"the storm checked more than it stepped (seed {seed})",
                  storm.checks > storm.steps)
    report.refuses("a storm without steps is refused",
                   lambda: run_storm(steps=0), WorkloadError)


def _edges(report: Report) -> None:
    report.section("empty and single-point trees answer without complaint")
    bare = KDTree()
    report.equal("the walk of nothing", bare.walk(), [])
    report.equal("nothing finds nothing", bare.nearest((0, 0)), None)
    report.equal("the plane of nothing", bare.range((-9, -9, 9, 9)), [])
    report.equal("nothing is held", bare.count(), 0)
    report.ok("nothing is seated", bare.invariant())
    report.ok("nothing answers membership", not bare.has((0, 0)))
    lone = KDTree([(3, 4)])
    report.equal("the lone point is its own answer", lone.nearest((0, 0)), (3, 4))
    report.equal("the lone point walks alone", lone.walk(), [(3, 4)])
    report.ok("the lone point answers membership", lone.has((3, 4)))
    report.ok("a neighbour is not the lone point", not lone.has((3, 5)))
    report.ok("the lone point is seated", lone.invariant())
    doubled = KDTree([(1, 1), (1, 1)])
    report.equal("a doubled point is seated once", doubled.count(), 1)


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
    _gate(report)
    _membership(report)
    _rectangles(report)
    _nearest(report)
    _rebuild(report)
    _corpora(report)
    _storms(report)
    _edges(report)
    _stories(report)
    return report
