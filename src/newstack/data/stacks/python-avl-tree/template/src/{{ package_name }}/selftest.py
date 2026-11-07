"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the keys can be trusted: the walk must
equal `sorted(live)` on seeded mixed workloads, every balance factor
must stay inside -1, 0, 1 after every move (checked from raw
structure, never assumed), rotations and rebuilds must preserve the
in-order sequence, and the height must stay under
ceil(1.44 * log2(n + 2)). Runnable in a fresh checkout:
`{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import brute_sort, factors, height_bound
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, KeysError, ensure_key
from .tree import AVLTree, TreeError

FIXTURE = "a rotation hands the height over"
KEYSETS = ((1, 2, 3, 4, 5), (5, 3, 8, 1, 4, 9, 2), (-7, 0, 7), tuple(range(64)))


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
    report.section("the gate keeps integers in and noise out")
    report.equal("a key comes back itself", ensure_key(-42), -42)
    report.equal("the largest key passes", ensure_key(MAX_KEY), MAX_KEY)
    report.refuses("a float is no key", lambda: ensure_key(1.5), KeysError)
    report.refuses("a string is no key", lambda: ensure_key("7"), KeysError)
    report.refuses("a bool is no key", lambda: ensure_key(True), KeysError)
    report.refuses(
        "one past the ceiling is no key", lambda: ensure_key(MAX_KEY + 1), KeysError
    )


def _order(report: Report) -> None:
    report.section("the walk is the plain sort, exactly")
    for keys in KEYSETS:
        tree = AVLTree(keys)
        report.equal(f"{keys[:3]}... walks the sort", tree.flatten(), brute_sort(keys))
        report.ok(f"{len(keys)} keys seated", tree.invariant())
        report.equal(f"{len(keys)} keys audit clean", tree.audit(), [])
    corpus = synthetic(40, seed=17)
    tree = AVLTree(corpus)
    report.equal("forty seeded keys walk the sort", tree.flatten(), brute_sort(corpus))
    live: set[int] = set()
    tree = AVLTree()
    for step, key in enumerate(corpus):
        tree.insert(key)
        live.add(key)
        if tree.flatten() != brute_sort(live):
            report.equal(f"mixed insert broke at {step}", "break", "none")
            return
    report.ok("forty inserts kept the walk at the sort", True)


def _balance(report: Report) -> None:
    report.section("every factor stays inside -1, 0, 1, checked")
    for keys in KEYSETS:
        tree = AVLTree(keys)
        report.ok(
            f"factors of {len(keys)} keys sit tight",
            all(abs(factor) <= 1 for factor in factors(tree._root)),
        )
    for count in (7, 31, 64, 128):
        tree = AVLTree(synthetic(count, seed=count))
        report.ok(
            f"a rebuild of {count} keeps factors tight",
            all(abs(factor) <= 1 for factor in factors(tree.rebuild()._root)),
        )
    report.equal("the rebuild keeps the walk", AVLTree(KEYSETS[1]).rebuild().flatten(),
                 brute_sort(KEYSETS[1]))


def _ceiling(report: Report) -> None:
    report.section("the height stays under the ceiling")
    report.equal("the bound of zero keys", height_bound(0), 2)
    report.equal("the bound of two keys", height_bound(2), 3)
    for count in (10, 64, 256, 1000):
        tree = AVLTree(synthetic(count, seed=count))
        report.ok(
            f"{count} keys reach at most {height_bound(count)}",
            tree.height <= height_bound(count),
        )
    rising = AVLTree(range(1, 200))
    report.equal("rising inserts walk sorted", rising.flatten(), list(range(1, 200)))
    report.ok("rising inserts stay under the bound",
              rising.height <= height_bound(199))


def _edges(report: Report) -> None:
    report.section("empty, single, and duplicated keys answer quietly")
    bare = AVLTree()
    report.equal("the empty tree walks empty", bare.flatten(), [])
    report.equal("the empty tree has no height", bare.height, 0)
    report.equal("the empty tree holds no key", 5 in bare, False)
    report.ok("the empty tree is seated", bare.invariant())
    one = AVLTree([7])
    report.equal("one key walks alone", one.flatten(), [7])
    report.equal("one key is looked up", 7 in one, True)
    report.equal("one key removes to empty", (one.remove(7), one.height)[1], 0)
    dup = AVLTree([1, 1, 1])
    report.equal("a double insert sat in once", dup.flatten(), [1])
    report.equal("a double insert kept size", len(dup), 1)
    tree = AVLTree([4, 8, 15])
    report.equal("seated keys stay seated", tree.insert(8) or 8 in tree, True)
    report.refuses("an absent remove is refused", lambda: tree.remove(99), TreeError)
    report.refuses("a float remove is refused", lambda: tree.remove(4.0), TreeError)
    report.equal("the refused remove changed nothing", tree.flatten(), [4, 8, 15])


def _corpora(report: Report) -> None:
    report.section("the key list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the keys are distinct", len(set(corpus)) == 20)
    report.refuses("no keys from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its keys", list(thawed.keys), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/keys.txt"
        write_keys(corpus, path)
        report.equal("a written list reads back", load_keys(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_keys(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7.5\n")
        report.refuses("a noisy list is refused", lambda: load_keys(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every move")
    from .workload import (
        WorkloadError,
        rebuild_matches,
        run_storm,
    )

    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.ok(
            f"the storm checked more than it stepped (seed {seed})",
            storm.checks > storm.steps,
        )
    report.ok("rebuilt trees answer alike", rebuild_matches([9, 40]))
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


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
    _order(report)
    _balance(report)
    _ceiling(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _stories(report)
    return report
