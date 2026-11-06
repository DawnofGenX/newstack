"""The promises this tree makes, run against the real modules.

Every claim here is the reason the answers are trustworthy: a stabbing and
an overlap answer must equal the brute-force scan on a seeded corpus, the
max-end augmentation must survive every delete, an empty tree answers
without complaint, and a point at a span's right end stands outside.
Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .corpus import CorpusError, load_spans, synthetic, write_spans
from .scan import scan_overlap, scan_stab
from .span import Interval, SpanError
from .tree import IntervalTree, TreeError

FIXTURE = "the right end is never reached"


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


def _stab_equal(tree: IntervalTree, spans: list[Interval], point: int) -> bool:
    return tree.stab(point) == scan_stab(spans, point)


def _overlap_equal(tree: IntervalTree, spans: list[Interval], low: int, high: int) -> bool:
    return tree.overlap(low, high) == scan_overlap(spans, low, high)


def _empty(report: Report) -> None:
    report.section("an empty tree answers without complaint")
    tree = IntervalTree()
    report.equal("the walk of nothing is nothing", tree.walk(), [])
    report.equal("a stab of nothing stabs nothing", tree.stab(0), [])
    report.equal("an overlap touches nothing", tree.overlap(-5, 5), [])
    report.equal("first finds nothing", tree.first(0), None)
    report.equal("height of nothing is zero", tree.height, 0)
    report.equal("deleting from nothing says no", tree.delete(Interval(0, 1)), False)
    report.equal("and nothing is broken", tree.audit(), [])


def _boundary(report: Report) -> None:
    report.section("half-open: the right end is never reached")
    tree = IntervalTree([Interval(1, 3), Interval(3, 5)])
    report.equal("a stab at the left end lands inside", tree.stab(1), [Interval(1, 3)])
    report.equal("a stab at the right end stands outside", tree.stab(3), [Interval(3, 5)])
    report.equal("touching spans do not overlap", tree.overlap(3, 4), [Interval(3, 5)])
    report.equal("a window ends before it touches", tree.overlap(0, 1), [])
    report.refuses("an empty span is refused", lambda: Interval(4, 4), SpanError)
    report.refuses("an inverted span is refused", lambda: Interval(5, 2), SpanError)


def _scan_agreement(report: Report) -> None:
    report.section("every answer equals the scan, on every seeded corpus")
    for seed in (7, 23, 91):
        spans = synthetic(80, seed=seed, low=-150, high=150)
        tree = IntervalTree(spans)
        rng = random.Random(seed * 11)
        for _ in range(60):
            point = rng.randrange(-160, 160)
            report.ok(f"seed {seed} stab {point} equals the scan", _stab_equal(tree, spans, point))
        for _ in range(30):
            low = rng.randrange(-160, 140)
            high = low + rng.randrange(1, 60)
            ok = _overlap_equal(tree, spans, low, high)
            report.ok(f"seed {seed} overlap [{low}..{high}) equals the scan", ok)
        report.equal(f"seed {seed} walks to the sorted corpus", tree.walk(), sorted(spans))
        report.equal(f"seed {seed} keeps its augmentation", tree.audit(), [])


def _augmentation(report: Report) -> None:
    report.section("deletion repairs the augmentation, always")
    for seed in (5, 41):
        spans = synthetic(60, seed=seed, low=-90, high=90)
        tree = IntervalTree(spans)
        rng = random.Random(seed * 7)
        shelf = list(spans)
        for _ in range(40):
            doomed = rng.choice(shelf)
            assert tree.delete(doomed)
            shelf.remove(doomed)
            report.ok(f"seed {seed} stays audited after a delete", tree.audit() == [])
            report.ok(
                f"seed {seed} still stabs like the shelf",
                _stab_equal(tree, shelf, rng.randrange(-90, 90)),
            )
        report.equal(f"seed {seed} shrinks to the shelf", sorted(tree.walk()), sorted(shelf))


def _insert_delete(report: Report) -> None:
    report.section("insert lands once, delete answers honestly")
    tree = IntervalTree()
    assert tree.insert(Interval(2, 9)) is True
    assert tree.insert(Interval(2, 9)) is False
    report.equal("a duplicate costs nothing", len(tree), 1)
    report.equal("a vanished span stays gone", tree.delete(Interval(0, 1)), False)
    report.equal("a held span leaves", tree.delete(Interval(2, 9)), True)
    report.equal("the tree is empty again", len(tree), 0)
    report.refuses(
        "a non-span is refused at the door",
        lambda: tree.insert((2, 9)),  # type: ignore[arg-type]
        TreeError,
    )


def _fixture(report: Report) -> None:
    report.section("span lists round-trip through the file")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as room:
        path = Path(room) / "spans.txt"
        spans = [Interval(-4, 2), Interval(0, 6), Interval(6, 9)]
        write_spans(spans, path)
        report.equal("a written list reads back", load_spans(path), spans)
        junk = Path(room) / "junk.txt"
        junk.write_text("two nine\n", encoding="utf-8")
        report.refuses("words are refused by name", lambda: load_spans(junk), CorpusError)
        empty = Path(room) / "empty.txt"
        empty.write_text("# nothing\n", encoding="utf-8")
        report.refuses("a comment-only list holds no spans", lambda: load_spans(empty), CorpusError)


def _marker(report: Report) -> None:
    report.section("the phrase the detector looks for ships in the code")
    from . import tree as tree_module

    joined = " ".join((tree_module.__doc__ or "").split())
    report.ok("the marker sits in the tree module docstring", FIXTURE in joined)


def run() -> Report:
    report = Report()
    _empty(report)
    _boundary(report)
    _scan_agreement(report)
    _augmentation(report)
    _insert_delete(report)
    _fixture(report)
    _marker(report)
    return report
