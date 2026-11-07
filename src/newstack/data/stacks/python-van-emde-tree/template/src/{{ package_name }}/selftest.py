"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the seats can be trusted: successor
must equal the smallest live key >= query, predecessor the largest
live key <= query, membership plain set membership — checked against
the shipped scans on seeded storms, never assumed. Runnable in a
fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import (
    scan_predecessor,
    scan_successor,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, UNIVERSE, KeysError, ensure_key
from .tree import TreeError, VanEmdeTree

FIXTURE = "cluster arithmetic pays the seek"
KEYSETS = ((0, 7, 255), (1, 2, 3, 4, 5), (0, 64, 128, 192), tuple(range(0, 256, 17)))


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
    report.section("the gate keeps seats in and noise out")
    report.equal("a seat comes back itself", ensure_key(200), 200)
    report.equal("the last seat passes", ensure_key(MAX_KEY), MAX_KEY)
    report.refuses("a float is no seat", lambda: ensure_key(1.5), KeysError)
    report.refuses("a string is no seat", lambda: ensure_key("7"), KeysError)
    report.refuses("a bool is no seat", lambda: ensure_key(True), KeysError)
    report.refuses("one past the universe is no seat", lambda: ensure_key(UNIVERSE), KeysError)
    report.refuses("below zero is no seat", lambda: ensure_key(-1), KeysError)


def _seeks(report: Report) -> None:
    report.section("successor and predecessor equal the scan, always")
    for keys in KEYSETS:
        tree = VanEmdeTree(keys)
        for query in range(MAX_KEY + 1):
            if tree.successor(query) != scan_successor(keys, query):
                report.equal(f"{keys[:2]}... succ broke at {query}", "break", "scan")
                return
            if tree.predecessor(query) != scan_predecessor(keys, query):
                report.equal(f"{keys[:2]}... pred broke at {query}", "break", "scan")
                return
        report.ok(f"{len(keys)} seats seek clean across the universe", True)
        report.ok(f"{len(keys)} seats audit clean", tree.invariant())


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every move")
    from .workload import (
        WorkloadError,
        rebuild_matches,
        run_storm,
    )

    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 160)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.equal(
            f"the storm settled every step (seed {seed})",
            storm.checks,
            storm.steps,
        )
    report.ok("rebuilt trees answer alike", rebuild_matches([9, 40, 250]))
    report.refuses("a storm without steps is refused", lambda: run_storm(steps=0),
                   WorkloadError)


def _edges(report: Report) -> None:
    report.section("empty, single, and doubled seats answer quietly")
    bare = VanEmdeTree()
    report.equal("the empty tree walks empty", bare.live(), [])
    report.equal("the empty tree has no min", bare.minimum(), None)
    report.equal("the empty tree seeks nothing", bare.successor(0), None)
    report.equal("the empty tree holds no seat", bare.member(0), False)
    report.ok("the empty tree is seated", bare.invariant())
    one = VanEmdeTree([7])
    report.equal("one seat walks alone", one.live(), [7])
    report.equal("one seat is looked up", one.member(7), True)
    report.equal("one seat seeks itself", one.successor(7), 7)
    report.equal("one seat is unseated", (one.remove(7), len(one))[1], 0)
    dup = VanEmdeTree([3, 3, 3])
    report.equal("a double insert sat once", dup.live(), [3])
    report.equal("a double insert kept size", len(dup), 1)
    tree = VanEmdeTree([4, 8, 15])
    report.refuses("an absent remove is refused", lambda: tree.remove(99), TreeError)
    report.equal("the refused remove changed nothing", tree.live(), [4, 8, 15])
    full = VanEmdeTree(range(MAX_KEY + 1))
    report.equal("the universe holds all seats", len(full), UNIVERSE)
    report.equal("the last seat succeeds itself", full.successor(MAX_KEY), MAX_KEY)
    report.equal("the first seat precedes itself", full.predecessor(0), 0)


def _corpora(report: Report) -> None:
    report.section("the key list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the seats are distinct", len(set(corpus)) == 20)
    report.refuses("no keys from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its keys", list(thawed.keys), corpus)
    report.refuses("half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
                   CorpusError)
    with TemporaryDirectory() as room:
        path = f"{room}/keys.txt"
        write_keys(corpus, path)
        report.equal("a written list reads back", load_keys(path), corpus)
        report.refuses("a missing list is named", lambda: load_keys(f"{room}/missing.txt"),
                       CorpusError)
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7.5\n")
        report.refuses("a noisy list is refused", lambda: load_keys(noise), CorpusError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import tree as tree_module

    report.ok(
        "the marker the detector looks for is in the tree module",
        FIXTURE in " ".join((tree_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _seeks(report)
    _storms(report)
    _edges(report)
    _corpora(report)
    _stories(report)
    return report
