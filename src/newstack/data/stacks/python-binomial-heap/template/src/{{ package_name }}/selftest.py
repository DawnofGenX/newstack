"""The invariants this forest promises, run against the real modules.

Every claim here is the reason the trees can be trusted: a tree of
rank k holds exactly 2^k keys, the forest stands one tree per rank,
the ranks are the bit pattern of the count, and meld of two heaps
drains as the sorted concat of their inputs. Runnable in a fresh
checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .heap import BinomialHeap, HeapError, Tree, link, ranks_of
from .keys import KeyValueError, bits, describe, ensure_key
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_keys,
    monotone,
    synthetic,
    write_keys,
)
from .workload import WorkloadError, run_meld, run_monotone, run_workload

FIXTURE = "one tree per rank"
KEYS = [-77, 0, 4, 15, 17, 30, 63, 64, 100, 255, 256, 500, 1023, 2047, 4095]


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


def _shape(report: Report) -> None:
    report.section("a tree of rank k holds exactly 2^k keys")
    tree = Tree(7, "seven")
    report.equal("a lone root is rank zero", tree.rank, 0)
    report.equal("a lone root holds one key", tree.count(), 1)
    left = Tree(3, None)
    right = Tree(9, None)
    joined = link(left, right)
    report.equal("a link is rank one", joined.rank, 1)
    report.equal("rank one holds two keys", joined.count(), 2)
    report.equal("the smaller root stayed on top", joined.key, 3)
    report.equal("the larger became its child", joined.children[0].key, 9)
    report.ok("rank one is ordered", joined.ordered())
    report.equal("rank zero bits", ranks_of(0), [])
    report.equal("seven is ranks 0, 1, 2", ranks_of(7), [0, 1, 2])
    report.equal("eight is rank three alone", ranks_of(8), [3])
    report.refuses("half a count is no shape", lambda: ranks_of(-1), HeapError)


def _drain(report: Report) -> None:
    report.section("pop-min answers sorted, and empty heaps refuse")
    heap = BinomialHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
    report.equal("the count is the count", len(heap), len(KEYS))
    report.equal("the forest stands as the bits", heap.shape(), ranks_of(len(KEYS)))
    report.equal("draining is the sorted corpus", list(heap.pop_all()), sorted(KEYS))
    report.ok("a drained heap holds nothing", not heap)
    report.refuses("an empty heap refuses to pop", lambda: BinomialHeap().pop(), HeapError)
    report.refuses(
        "an empty heap refuses to peek", lambda: BinomialHeap().peek(), HeapError
    )


def _meld(report: Report) -> None:
    report.section("meld is the product plain heaps refuse")
    left = BinomialHeap()
    right = BinomialHeap()
    for key in (5, 1, 9):
        left.push(key, key)
    for key in (-4, 12, 300, 700):
        right.push(key, key)
    left.meld(right)
    report.equal("the union counts both", len(left), 7)
    report.equal("the emptied heap holds nothing", len(right), 0)
    report.equal("the forest is the bit pattern", left.shape(), ranks_of(7))
    report.equal("pop-min is the min of the union", left.peek()[0], -4)
    report.equal("the drain is the sorted concat", list(left.pop_all()), sorted(
        [5, 1, 9, -4, 12, 300, 700]
    ))
    report.refuses("a heap will not meld with itself", lambda: left.meld(left), HeapError)
    report.refuses("a flag is no key", lambda: left.push(True), HeapError)


def _storms(report: Report) -> None:
    report.section("the storms, replayed against the sorted truth")
    storm = run_workload(seed=13)
    report.equal("the mixed storm ran its steps", storm.steps, 160)
    report.equal("the mixed storm broke no invariant", storm.breaks, 0)
    report.ok("the mixed storm answered the pool", storm.sorted_held)
    report.ok("the storm melded on the way", storm.melds > 0)
    report.ok("the storm checked more than it stepped", storm.checks > storm.steps)
    pair = run_meld(seed=11, left=50, right=37)
    report.ok("a meld drains as the sorted concat", pair.sorted_held)
    report.ok("a melded forest stands as the bits", pair.shapes_held)
    forward = run_monotone(seed=11, size=64)
    report.equal("a rising stream breaks nothing", forward.breaks, 0)
    report.ok("a rising stream answers sorted", forward.sorted_held)
    report.refuses(
        "a storm outside its bounds is refused", lambda: run_workload(steps=0),
        WorkloadError,
    )


def _seating(report: Report) -> None:
    report.section("every op leaves the bit pattern standing")
    heap = BinomialHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
        report.ok(f"push {key} left the bits true", heap.shape() == ranks_of(len(heap)))
    for _ in range(6):
        heap.pop()
        report.ok("a pop left the bits true", heap.shape() == ranks_of(len(heap)))
    report.ok("the forest kept its rank rule", heap.invariant())
    report.equal("the survivors drain sorted", list(heap.pop_all()), sorted(KEYS)[6:])


def _streams(report: Report) -> None:
    report.section("the stream in and the snapshot out")
    pairs = synthetic(60, seed=5)
    report.equal("the generator is deterministic", pairs, synthetic(60, seed=5))
    report.ok("the keys are distinct", len({key for key, _ in pairs}) == 60)
    report.ok("a forest takes negative keys", any(key < 0 for key, _ in pairs))
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), StreamError)
    rising = monotone(32, seed=4)
    report.equal("the monotone stream rises", [key for key, _ in rising],
                 sorted(key for key, _ in rising))
    frozen = Snapshot(pairs, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its pairs", thawed.pairs, pairs)
    report.equal("a snapshot keeps its seed", thawed.seed, DEFAULT_SEED)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        StreamError,
    )
    with TemporaryDirectory() as room:
        path = f"{room}/keys.txt"
        write_keys(pairs, path)
        report.equal("a written stream reads back", load_keys(path), pairs)
        report.refuses(
            "a missing stream is named", lambda: load_keys(f"{room}/missing.txt"),
            StreamError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1 x\n")
        report.refuses("a stream of noise is refused", lambda: load_keys(noise), StreamError)


def _keys(report: Report) -> None:
    report.section("the forest orders whole numbers")
    report.equal("the key comes back itself", ensure_key(7), 7)
    report.equal("a negative key is whole", ensure_key(-77), -77)
    report.equal("a key renders as itself", describe(42), "42")
    report.equal("forty-six is 101110", bits(46), "101110")
    report.equal("zero is 0", bits(0), "0")
    report.refuses("a negative count has no bits", lambda: bits(-1), KeyValueError)
    report.refuses("a flag is no key", lambda: ensure_key(True), KeyValueError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import heap as heap_module

    report.ok(
        "the marker the detector looks for is in the heap module",
        FIXTURE in " ".join((heap_module.__doc__ or "").split()),
    )


def run() -> Report:
    report = Report()
    _shape(report)
    _drain(report)
    _meld(report)
    _seating(report)
    _storms(report)
    _streams(report)
    _keys(report)
    _stories(report)
    return report
