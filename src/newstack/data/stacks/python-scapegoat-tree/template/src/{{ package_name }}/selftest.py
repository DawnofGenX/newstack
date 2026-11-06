"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the shape can be trusted: the answers
must equal bisect's, the alpha rule must hold on every node after
every rebuild-triggering op of a seeded storm, a rebuild must be
lossless — the sorted run identical before and after — and the work
counter must track n log n while one insert may still charge linear.
Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from random import Random

from .keys import KeyValueError, describe, ensure_key
from .rules import (
    DEFAULT_ALPHA,
    RuleError,
    checked_alpha,
    depth_bound,
    heavy_child,
    lower_child,
    violates,
    worst_case_rebuild,
)
from .streams import Snapshot, StreamError, load_keys, synthetic, write_keys
from .tree import ScapegoatTree, TreeError, flatten

FIXTURE = "a tipped subtree is flattened and rebuilt whole"
KEYS = [
    -498,
    -400,
    -379,
    -285,
    -206,
    -173,
    -70,
    -40,
    2,
    24,
    69,
    100,
    136,
    195,
    269,
    302,
    362,
    412,
    475,
]


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


def _rules(report: Report) -> None:
    report.section("the rule is arithmetic, not a rumour")
    report.equal("alpha defaults to seven tenths", DEFAULT_ALPHA, 0.7)
    report.equal("a parent of ninety tolerates sixty-two", heavy_child(0.7, 90), 62)
    report.equal("a rebuild lands a ninety-parent on twenty-seven", lower_child(0.7, 90), 27)
    report.ok("sixty-three tips ninety", violates(0.7, 63, 90))
    report.ok("sixty-two holds at ninety", not violates(0.7, 62, 90))
    report.equal("the worst bill is the heaviest tolerated child", worst_case_rebuild(0.7, 90), 62)
    report.equal("the depth promise counts the log", depth_bound(0.7, 45), 12)
    report.refuses("alpha one keeps no rule", lambda: checked_alpha(1.0), RuleError)
    report.refuses("alpha zero keeps no rule", lambda: checked_alpha(0.0), RuleError)
    report.refuses("no keys stand no promise", lambda: depth_bound(0.7, 0), RuleError)


def _keys(report: Report) -> None:
    report.section("the order is decided once")
    report.equal("the key comes back itself", ensure_key(7), 7)
    report.ok("int and float share a slot", ensure_key(1) == ensure_key(1.0))
    report.equal("a string renders itself", describe("ladder"), "ladder")
    report.refuses("a list has no place in the order", lambda: ensure_key([1]), KeyValueError)


def _tree(report: Report) -> None:
    report.section("the tree answers what bisect answers")
    tree = ScapegoatTree()
    for index, key in enumerate(KEYS):
        tree.insert(key, index)
    report.equal("iteration is the sorted order", list(tree.keys()), sorted(KEYS))
    report.equal("size counts keys", len(tree), len(KEYS))
    for probe in (-499, -400, 30, 300, 476):
        report.equal(
            f"rank answers for {probe}", tree.rank(probe), bisect.bisect_left(KEYS, probe)
        )
    for position in (0, 9, len(KEYS) - 1):
        report.equal(
            "select lands where rank sent it",
            tree.rank(tree.select(position)[0]),
            position,
        )
    report.equal("the tree holds what went in", tree.get(KEYS[9]), 9)
    report.ok(
        "a repeat replaces the value, not the tree",
        (tree.insert(KEYS[9], "new"), tree.get(KEYS[9]))[1] == "new",
    )
    report.equal("a repeat did not grow the tree", len(tree), len(KEYS))
    report.ok("the settled tree holds the rule", tree.balanced())
    report.ok(
        "depth keeps the promise", tree.depth() <= depth_bound(tree.alpha, len(tree))
    )
    report.refuses("a position past the tree is refused", lambda: tree.select(len(tree)), TreeError)
    report.refuses("a negative position is refused", lambda: tree.select(-1), TreeError)


def _storm(report: Report) -> None:
    report.section("a mixed storm re-checks the rule after every op")
    rng = Random(13)
    live: list[int] = []
    tree = ScapegoatTree()
    breaks = 0
    slips = 0
    for _ in range(160):
        roll = rng.random()
        if roll < 0.45:
            key = rng.choice(KEYS)
            tree.insert(key, 1)
            live = sorted(set(live) | {key})
        elif roll < 0.65 and live:
            key = rng.choice(live)
            tree.delete(key)
            live = [x for x in live if x != key]
        elif roll < 0.85:
            key = rng.choice(KEYS)
            if tree.rank(key) != bisect.bisect_left(live, key):
                breaks += 1
        elif live:
            spot = rng.randrange(len(live))
            if tree.select(spot)[0] != live[spot]:
                breaks += 1
        if live:
            if not tree.balanced():
                breaks += 1
            if [key for key, _ in flatten(tree.root)] != live:
                breaks += 1
            if tree.depth() > depth_bound(DEFAULT_ALPHA, len(live)):
                slips += 1
    report.equal("the storm broke nothing", breaks, 0)
    report.equal("depth kept the promise through the storm", slips, 0)
    report.ok("the storm left keys standing", len(live) > 0)


def _rebuild(report: Report) -> None:
    report.section("the rebuild is lossless")
    tree = ScapegoatTree()
    for index in range(64):
        tree.insert(index, index)
    before = [key for key, _ in flatten(tree.root)]
    from .tree import _rebuild as midpoint

    fresh = flatten(midpoint(flatten(tree.root), 0, len(tree)))
    report.equal("flattening returns the run the tree kept", [k for k, _ in fresh], before)
    report.equal("the rebuild kept every key", len(fresh), 64)
    rebuilt = ScapegoatTree()
    rebuilt.root = midpoint(flatten(tree.root), 0, len(tree))
    report.ok("a midpoint tree holds the rule", rebuilt.balanced())
    report.ok(
        "the rebuild is only as big as the heaviest child",
        worst_case_rebuild(0.7, len(tree)) <= len(tree),
    )


def _counter(report: Report) -> None:
    report.section("the counter settles at n log n, not n n")
    marks: list[int] = []
    for size in (100, 200, 400):
        tree = ScapegoatTree()
        for index in range(size):
            tree.insert(index, index)
        marks.append(tree.work)
    first = marks[1] / marks[0]
    second = marks[2] / marks[1]
    report.ok(f"first doubling costs {first:.2f}x, under quadratic", first < 3.0)
    report.ok(f"second doubling costs {second:.2f}x, under quadratic", second < 3.0)
    single = ScapegoatTree()
    for index in range(64):
        single.insert(index, index)
    charge = single.work
    single.insert(200, 200)
    report.ok("one insert still charges a real bill", single.work > charge)
    report.equal("the stream answer holds the rule", int(single.balanced()), 1)


def _streams(report: Report) -> None:
    report.section("streams in, snapshots out")
    pairs = synthetic(24, seed=11)
    report.equal("one seed hands one stream", synthetic(24, seed=11), pairs)
    report.ok("the stream is distinct keys", len({key for key, _ in pairs}) == 24)
    frozen = Snapshot(pairs, 0.7)
    report.equal("a snapshot replays itself", Snapshot.loads(frozen.dumps()).pairs, pairs)
    report.refuses("a stream of one is no tree size", lambda: synthetic(0), StreamError)
    report.refuses("a noise snapshot is refused", lambda: Snapshot.loads("[]"), StreamError)
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as work:
        path = f"{work}/keys.txt"
        write_keys(pairs, path)
        report.equal("a written stream reads back", load_keys(path), pairs)
        report.refuses(
            "a missing stream is unusable",
            lambda: load_keys(f"{work}/gone"),
            StreamError,
        )


def _stories(report: Report) -> None:
    report.section("the six stories hold")
    from .demo import run_stories

    for story in run_stories():
        report.ok(f"{story.title} holds", story.held)
    from . import tree as tree_module

    report.ok(
        "the marker the detector looks for is in the tree module",
        FIXTURE in " ".join((tree_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _rules(report)
    _keys(report)
    _tree(report)
    _storm(report)
    _rebuild(report)
    _counter(report)
    _streams(report)
    _stories(report)
    return report
