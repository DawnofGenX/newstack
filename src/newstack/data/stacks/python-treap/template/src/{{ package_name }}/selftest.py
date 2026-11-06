"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the shape can be trusted: the search
order and the heap floor must both hold after every op of a seeded
storm, `rank` must answer exactly what `bisect` answers, and a split
must lose nothing the join does not hand back. Runnable in a fresh
checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .draws import DEFAULT_SEED, DrawError, Draws, expected_depth
from .keys import KeyValueError, describe, ensure_key
from .streams import Snapshot, StreamError, load_keys, synthetic, write_keys
from .treap import Treap, TreapError
from .workload import WorkloadError, run_workload

FIXTURE = "a draw decides who stands above"
KEYS = list(range(-40, 41, 3))


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


def _draws(report: Report) -> None:
    report.section("the draws are the only randomness")
    draws = Draws(seed=7)
    twin = Draws(seed=7)
    report.equal("one seed hands one key one number",
                 draws.shape_of("ladder"), twin.shape_of("ladder"))
    report.ok("draws rise in count as they are asked", draws.count == 1)
    report.equal("the depth promise tracks the bits", expected_depth(1024), 12)
    report.refuses("a seed must be a number", lambda: Draws("seven"), DrawError)
    report.refuses("zero keys stand no tree", lambda: expected_depth(0), DrawError)


def _keys(report: Report) -> None:
    report.section("the order is decided once")
    report.equal("the key comes back itself", ensure_key(7), 7)
    report.ok("int and float share a slot", ensure_key(1) == ensure_key(1.0))
    report.equal("a string renders itself", describe("towers"), "towers")
    report.equal("an integral float prints as an int", describe(3.0), "3")
    report.refuses("a list has no place in the order", lambda: ensure_key([1]), KeyValueError)


def _tree(report: Report) -> None:
    report.section("the tree answers what bisect answers")
    filled = Treap(seed=DEFAULT_SEED)
    for index, key in enumerate(KEYS):
        filled.insert(key, index)
    report.equal("iteration is the sorted order", list(filled.keys()), sorted(KEYS))
    report.equal("size counts keys", len(filled), len(KEYS))
    for probe in (-41, -39, 0, 7, 40, 41):
        report.equal(
            f"rank answers for {probe}", filled.rank(probe), bisect.bisect_left(KEYS, probe)
        )
    for position in (0, 9, len(KEYS) - 1):
        report.equal(
            "select lands where rank sent it",
            filled.rank(filled.select(position)[0]),
            position,
        )
    report.equal("the tree holds what went in", filled.get(KEYS[9]), 9)
    report.ok(
        "a repeat replaces the value, not the draw",
        (filled.insert(KEYS[9], "new"), filled.get(KEYS[9]))[1] == "new",
    )
    report.equal("a repeat did not grow the tree", len(filled), len(KEYS))
    report.ok("predecessor stops at the front", filled.predecessor(min(KEYS)) is None)
    report.ok("successor stops at the back", filled.successor(max(KEYS)) is None)
    report.refuses(
        "a position past the tree is refused",
        lambda: filled.select(len(filled)),
        TreapError,
    )
    report.refuses("a backwards window is refused", lambda: filled.window(9, 3), TreapError)
    report.equal(
        "the window holds its bounds",
        [key for key, _ in filled.window(-10, 10)],
        [key for key in KEYS if -10 <= key <= 10],
    )
    report.equal("neither order broke in the fill", filled.stats()["broken"], (0, 0))


def _workload(report: Report) -> None:
    report.section("a mixed storm re-checks both orders")
    replay = run_workload(seed=13)
    report.equal("the storm ran its steps", replay.steps, 160)
    report.equal("every op left both orders intact", replay.breaks, 0)
    report.ok("the storm checked more than it stepped", replay.checks > replay.steps)
    report.equal("the replay is a replay", run_workload(seed=13), replay)
    report.refuses(
        "a storm outside its bounds is refused",
        lambda: run_workload(size=0),
        WorkloadError,
    )


def _split(report: Report) -> None:
    report.section("a split loses nothing the join returns")
    filled = Treap(seed=5)
    for index, key in enumerate(KEYS):
        filled.insert(key, index)
    pivot = 3
    under, over = filled.split(pivot)
    report.equal(
        "the left half is the keys below",
        list(under.keys()),
        [key for key in KEYS if key < pivot],
    )
    report.equal(
        "the right half is the pivot and above",
        list(over.keys()),
        [key for key in KEYS if key >= pivot],
    )
    joined = Treap.join(under, over)
    report.equal("the join restores the keys", joined.pairs(), filled.pairs())
    report.equal(
        "the join restores the exact shape",
        joined.stats()["walk"],
        filled.stats()["walk"],
    )
    report.refuses(
        "overlapping halves are refused",
        lambda: Treap.join(filled, over),
        TreapError,
    )


def _seeds(report: Report) -> None:
    report.section("the seed owns the shape")
    left = Treap(seed=3)
    right = Treap(seed=3)
    for index, key in enumerate(KEYS):
        left.insert(key, index)
        right.insert(key, index)
    report.equal("same seed leaves same tree", left.stats()["walk"], right.stats()["walk"])
    twin = left.rebuild()
    report.equal(
        "a rebuild from entries replays the shape",
        twin.stats()["walk"],
        left.stats()["walk"],
    )
    report.equal("the replay answers the same", twin.pairs(), left.pairs())
    other = Treap(seed=4)
    for key, value in left.pairs():
        other.insert(key, value)
    report.equal("another seed keeps the order", other.pairs(), left.pairs())
    report.ok("another seed shuffles the shape", other.stats()["walk"] != left.stats()["walk"])


def _streams(report: Report) -> None:
    report.section("the stream in and the snapshot out")
    pairs = synthetic(60, seed=5)
    report.equal("the generator is deterministic", pairs, synthetic(60, seed=5))
    report.ok("the keys are distinct", len({key for key, _ in pairs}) == 60)
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), StreamError)
    frozen = Snapshot(pairs, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its pairs", thawed.pairs, pairs)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), StreamError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/keys.txt"
        write_keys(pairs, path)
        report.equal("a written stream reads back", load_keys(path), pairs)
        report.refuses(
            "a missing stream is named", lambda: load_keys(f"{room}/missing.txt"), StreamError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1 x\n")
        report.refuses("a stream of noise is refused", lambda: load_keys(noise), StreamError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import draws as draws_module

    report.ok(
        "the marker the detector looks for is in the draws module",
        FIXTURE in " ".join((draws_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _draws(report)
    _keys(report)
    _tree(report)
    _workload(report)
    _split(report)
    _seeds(report)
    _streams(report)
    _stories(report)
    return report
