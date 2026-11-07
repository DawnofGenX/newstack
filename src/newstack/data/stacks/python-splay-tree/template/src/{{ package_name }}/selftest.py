"""The invariants this tree promises, run against the real modules.

Every claim here is the reason the keys can be trusted: the walk
must equal `sorted(live)` on seeded mixed workloads, every access
must leave the touched key at the root (the splay promise, checked
after every move, never assumed), a splay must preserve the in-order
walk, min and max must ride to the root on request, and an absent
remove must be refused. Runnable in a fresh checkout:
`python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import brute_sort, is_root
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, KeysError, ensure_key
from .tree import SplayTree, TreeError

FIXTURE = "a splay hands the root over"
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
        tree = SplayTree(keys)
        report.equal(f"{keys[:3]}... walks the sort", tree.flatten(), brute_sort(keys))
        report.ok(f"{len(keys)} keys seated", tree.invariant())
        report.equal(f"{len(keys)} keys audit clean", tree.audit(), [])
    corpus = synthetic(40, seed=17)
    live: set[int] = set()
    tree = SplayTree()
    for step, key in enumerate(corpus):
        tree.insert(key)
        live.add(key)
        if tree.flatten() != brute_sort(live):
            report.equal(f"mixed insert broke at {step}", "break", "none")
            return
        if not is_root(tree, key):
            report.equal(f"insert forgot the ride at {step}", "break", "none")
            return
    report.ok("forty inserts kept the walk at the sort and the rider up", True)


def _promise(report: Report) -> None:
    report.section("the splay promise, checked after every access")
    for keys in KEYSETS:
        tree = SplayTree(keys)
        for key in keys:
            if not (tree.contains(key) and is_root(tree, key)):
                report.equal(f"a touch of {key} left the root", "stray", "rooted")
                return
        report.ok(f"every touch of {len(keys)} keys ended at the root", True)
    ladder = SplayTree(list(range(1, 13)))
    for key in (1, 12, 6, 3, 9):
        ladder.contains(key)
        report.equal(f"the ride of {key} parked at the root", ladder.root, key)
    deep = SplayTree(list(range(1, 41)))
    walked_before = deep.flatten()
    deep.contains(1)
    report.equal("a deep zig-zig walk survived", deep.flatten(), walked_before)
    report.equal("a deep zig-zig ride reached the root", deep.root, 1)
    report.ok("the deep tree stays seated", deep.invariant())


def _request(report: Report) -> None:
    report.section("min and max ride to the root on request")
    for keys in KEYSETS:
        tree = SplayTree(keys)
        report.equal(f"min of {len(keys)} rides up", tree.minimum(), min(keys))
        report.equal("the min sits at the root", tree.root, min(keys))
        report.equal(f"max of {len(keys)} rides up", tree.maximum(), max(keys))
        report.equal("the max sits at the root", tree.root, max(keys))
        report.ok("the requested tree stays seated", tree.invariant())
    report.equal("the walk of a requested tree is the sort", tree.flatten(), brute_sort(keys))


def _walk(report: Report) -> None:
    report.section("a splay preserves the in-order walk")
    for keys in KEYSETS:
        tree = SplayTree(keys)
        before = tree.flatten()
        for key in keys:
            tree.contains(key)
            if tree.flatten() != before:
                report.equal(f"a splay of {key} moved the walk", "shifted", "still")
                return
        report.ok(f"{len(keys)} splays kept the walk", True)
    rebuilt = SplayTree(KEYSETS[1]).rebuild()
    report.equal("a rebuild answers alike", rebuilt.flatten(), brute_sort(KEYSETS[1]))
    report.ok("the rebuild stays seated", rebuilt.invariant())


def _edges(report: Report) -> None:
    report.section("empty, single, and duplicated keys answer quietly")
    bare = SplayTree()
    report.equal("the empty tree walks empty", bare.flatten(), [])
    report.equal("the empty tree has no root", bare.root, None)
    report.equal("the empty tree holds no key", 5 in bare, False)
    report.refuses("min of nothing is refused", bare.minimum, TreeError)
    report.refuses("max of nothing is refused", bare.maximum, TreeError)
    report.ok("the empty tree is seated", bare.invariant())
    one = SplayTree([7])
    report.equal("one key walks alone", one.flatten(), [7])
    report.equal("one key is looked up", one.contains(7), True)
    report.equal("one key removes to empty", (one.remove(7), one.root)[1], None)
    dup = SplayTree([1, 1, 1])
    report.equal("a double insert sat in once", dup.flatten(), [1])
    report.equal("a double insert kept size", len(dup), 1)
    report.equal("a double insert still rides", dup.root, 1)
    tree = SplayTree([4, 8, 15])
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


def _tangles(report: Report) -> None:
    report.section("the tangle: a ride checked move by move")
    for seed in (5, 31):
        rng = random.Random(seed)
        pool = synthetic(24, seed=seed)
        tree = SplayTree(pool)
        kept = 0
        broke = False
        for _ in range(80):
            key = rng.choice(pool)
            walk = tree.flatten()
            tree.contains(key)
            if tree.root != key or tree.flatten() != walk:
                broke = True
                break
            kept += 1
        report.ok(f"eighty tangles ended at the root (seed {seed})",
                  not broke and kept == 80)


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
    _promise(report)
    _request(report)
    _walk(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
