"""The invariants this heap promises, run against the real modules.

Every claim here is the reason the keys can be trusted: the drain
order must equal `sorted(pushed)` on seeded push/pop storms, the
parent rule must hold after every operation (the shipped checker
walks the array), the head must be the minimum of the live multiset,
and an empty pop must be refused. Runnable in a fresh checkout:
`python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .heap import HeapError, MinHeap
from .keys import MAX_KEY, KeysError, ensure_key
from .oracle import brute_drain, child_indices, heap_breaks, parent_index

FIXTURE = "the parent rides no higher"
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


def _shape(report: Report) -> None:
    report.section("the shipped checker walks the array")
    report.equal("the root has no parent", parent_index(0), -1)
    report.equal("slot seven sits under three", parent_index(7), 3)
    report.equal("slot three answers for seven", child_indices(3, 8), (7,))
    report.equal("slot three answers for both children", child_indices(3, 9), (7, 8))
    report.equal("a leaf answers for no children", child_indices(5, 6), ())
    report.equal("an honest array breaks nowhere", heap_breaks([1, 2, 3, 4, 5]), [])
    report.equal("a sunk parent is named", heap_breaks([3, 1, 2]), [0])
    report.equal("a parent above a smaller last slot is named", heap_breaks([1, 2, 3, 0]), [1])


def _drain(report: Report) -> None:
    report.section("the drain is the plain sort, exactly")
    for keys in KEYSETS:
        heap = MinHeap(keys)
        report.equal(f"{keys[:3]}... drains the sort", heap.drain(), brute_drain(keys))
        report.equal(f"{len(keys)} keys leave nothing behind", len(heap), 0)
    report.equal("repeats drain one per seat", MinHeap([4, 4, 1, 4]).drain(), [1, 4, 4, 4])


def _rule(report: Report) -> None:
    report.section("the parent rule holds after every operation")
    for keys in KEYSETS:
        heap = MinHeap()
        for key in keys:
            heap.push(key)
            if heap.breaks():
                report.equal(f"a push of {key} broke the rule", "break", "none")
                return
        while heap:
            heap.pop()
            if heap.breaks():
                report.equal("a pop broke the rule", "break", "none")
                return
        report.equal(f"{len(keys)} pushes and pops kept the rule", [], [])
    report.ok("the marker the detector looks for is in the heap module",
              FIXTURE in " ".join((MinHeap.__doc__ or "").split()).lower())


def _head(report: Report) -> None:
    report.section("the head is the minimum of the live bag")
    for keys in KEYSETS:
        heap = MinHeap(keys)
        live = list(keys)
        while live:
            if heap.peek() != min(live):
                report.equal("the head strayed from the minimum", "stray", "minimum")
                return
            got = heap.pop()
            live.remove(got)
        report.equal(f"{len(keys)} peeks answered the minimum", len(heap), 0)


def _edges(report: Report) -> None:
    report.section("empty, single, and repeated keys answer quietly")
    bare = MinHeap()
    report.equal("the empty heap holds nothing", len(bare), 0)
    report.refuses("pop of nothing is refused", bare.pop, HeapError)
    report.refuses("peek of nothing is refused", bare.peek, HeapError)
    report.equal("the empty heap drains empty", bare.drain(), [])
    report.equal("a refused pop took nothing", len(bare), 0)
    one = MinHeap([7])
    report.equal("one key peeks itself", one.peek(), 7)
    report.equal("one key pops itself", one.pop(), 7)
    report.equal("the emptied heap is empty", len(one), 0)
    dup = MinHeap([3, 3, 3])
    report.equal("a repeat drains every seat", dup.drain(), [3, 3, 3])
    report.equal("the drained repeat heap is empty", len(dup), 0)
    reborn = MinHeap()
    reborn.push(5)
    report.equal("an emptied heap takes keys again", reborn.peek(), 5)


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
        report.ok(f"the storm checked more than it stepped (seed {seed})",
                  storm.checks > storm.steps)
        report.ok(f"the storm pushed and popped (seed {seed})",
                  storm.pushes > 0 and storm.pops > 0)
    report.ok("rebuilt heaps answer alike", rebuild_matches([9, 40, -3]))
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


def _tangles(report: Report) -> None:
    report.section("the tangle: a peek checked move by move")
    for seed in (5, 31):
        rng = random.Random(seed)
        pool = synthetic(24, seed=seed)
        heap = MinHeap(pool)
        live = list(pool)
        broke = False
        for _ in range(80):
            if rng.random() < 0.5 or not live:
                key = rng.choice(pool)
                heap.push(key)
                live.append(key)
            else:
                got = heap.pop()
                live.remove(got)
            if heap.breaks() or (live and heap.peek() != min(live)):
                broke = True
                break
        report.ok(f"eighty tangles kept the head at the minimum (seed {seed})",
                  not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)


def run() -> Report:
    report = Report()
    _gate(report)
    _shape(report)
    _drain(report)
    _rule(report)
    _head(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _tangles(report)
    _stories(report)
    return report
