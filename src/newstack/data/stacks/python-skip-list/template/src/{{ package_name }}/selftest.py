"""The invariants this map promises, run against the real modules.

Every claim here is the reason the widths can be trusted: `rank` must
answer exactly what `bisect` answers, the towers must replay from their
seed, and a delete must repair every width it broke. Runnable in a
fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .coins import DEFAULT_SEED, CoinToss, CoinTossError, expected_level
from .keys import SkipKeyValueError, describe, ensure_key
from .map import SkipList, SkipListError
from .stack import CorpusError, Snapshot, load_pairs, synthetic, write_pairs

FIXTURE = "a coin decides how tall a tower may stand"
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
        body = "\n".join(self.lines)
        return f"{body}\n\nselftest: {self.checks} checks passed, {self.failed} failed"


def _coins(report: Report) -> None:
    report.section("the flips are the only randomness")
    toss = CoinToss(seed=7)
    twin = CoinToss(seed=7)
    report.equal("one seed replays one ladder", toss.plan(40).levels, twin.plan(40).levels)
    report.ok(
        "a level never outruns its cap",
        all(level < 4 for level in CoinToss(7, cap=4).plan(60).levels),
    )
    report.equal("expected level tracks log2", expected_level(1024), 11)
    report.equal("a single key stands one story", expected_level(1), 1)
    report.refuses(
        "a seed must be a number", lambda: CoinToss(seed="seven"), CoinTossError
    )  # type: ignore[arg-type]
    report.refuses("a cap of zero holds no tower", lambda: CoinToss(cap=0), CoinTossError)


def _keys(report: Report) -> None:
    report.section("the order is decided once")
    report.equal("the key comes back itself", ensure_key(7), 7)
    report.ok("int and float share a slot", ensure_key(1) == ensure_key(1.0))
    report.equal("a string renders itself", describe("towers"), "towers")
    report.equal("an integral float prints as an int", describe(3.0), "3")
    report.refuses("a list has no place in the order", lambda: ensure_key([1]), SkipKeyValueError)


def _map(report: Report) -> None:
    report.section("the map answers what bisect answers")
    filled = SkipList(seed=DEFAULT_SEED)
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
    report.equal("the map holds what went in", filled.get(KEYS[9]), 9)
    report.ok(
        "a repeat replaces the value, not the slot",
        (filled.insert(KEYS[9], "new"), filled.get(KEYS[9]))[1] == "new",
    )
    report.equal("a repeat did not grow the map", len(filled), len(KEYS))
    report.ok("predecessor stops at the front", filled.predecessor(min(KEYS)) is None)
    report.ok("successor stops at the back", filled.successor(max(KEYS)) is None)
    report.refuses(
        "a position past the map is refused",
        lambda: filled.select(len(KEYS)),
        SkipListError,
    )
    report.refuses(
        "a backwards window is refused", lambda: filled.window(9, 3), SkipListError
    )
    report.equal(
        "the window holds its bounds",
        [key for key, _ in filled.window(-10, 10)],
        [key for key in KEYS if -10 <= key <= 10],
    )


def _widths(report: Report) -> None:
    report.section("a delete repairs every width it broke")
    filled = SkipList(seed=13)
    for index, key in enumerate(KEYS):
        filled.insert(key, index)
    doomed = KEYS[::3]
    for key in doomed:
        filled.delete(key)
    survived = [key for key in KEYS if key not in set(doomed)]
    report.equal("the map shrank by the deletions", len(filled), len(survived))
    report.equal("iteration is still sorted order", list(filled.keys()), survived)
    mismatches = sum(
        1 for probe in survived if filled.rank(probe) != bisect.bisect_left(survived, probe)
    )
    report.equal("rank still matches bisect after the wreck", mismatches, 0)
    report.equal(
        "a vanished key leaves no rank ghost",
        filled.rank(doomed[0]),
        bisect.bisect_left(survived, doomed[0]),
    )
    report.equal(
        "deleting twice changes nothing twice", filled.delete(doomed[0]).changed, False
    )
    stats = filled.stats()
    report.ok(
        "the towers stay near the log2 promise",
        int(stats["tallest"]) <= expected_level(len(filled)) + 4,
    )


def _seeds(report: Report) -> None:
    report.section("the seed owns the shape")
    left = SkipList(seed=3)
    right = SkipList(seed=3)
    for index, key in enumerate(KEYS):
        left.insert(key, index)
        right.insert(key, index)
    report.equal("same seed leaves same shape", left.stats()["levels"], right.stats()["levels"])
    twin = left.rebuild()
    report.equal("the replay answers the same", twin.pairs(), left.pairs())
    other = SkipList(seed=4)
    for key, value in left.pairs():
        other.insert(key, value)
    report.equal("another seed keeps the order", other.pairs(), left.pairs())
    report.ok("another seed shuffles the shape", other.stats()["levels"] != left.stats()["levels"])


def _stack(report: Report) -> None:
    report.section("the stream in and the snapshot out")
    pairs = synthetic(60, seed=5)
    report.equal("the generator is deterministic", pairs, synthetic(60, seed=5))
    report.ok("the keys are distinct", len({key for key, _ in pairs}) == 60)
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(pairs, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its pairs", thawed.pairs, pairs)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/pairs.txt"
        write_pairs(pairs, path)
        report.equal("a written stream reads back", load_pairs(path), pairs)
        report.refuses(
            "a missing stream is named", lambda: load_pairs(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1 x\n")
        report.refuses("a stream of noise is refused", lambda: load_pairs(noise), CorpusError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import coins as coins_module

    report.ok(
        "the marker the detector looks for is in the coins module",
        FIXTURE in " ".join((coins_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _coins(report)
    _keys(report)
    _map(report)
    _widths(report)
    _seeds(report)
    _stack(report)
    _stories(report)
    return report
