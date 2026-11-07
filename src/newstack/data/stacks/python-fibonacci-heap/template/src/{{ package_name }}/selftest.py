"""The invariants this forest promises, run against the real modules.

Every claim here is the reason the keys can be trusted: the pop
sequence must equal `sorted(corpus with final keys)` on seeded mixed
streams, every degree must stay under the documented log bound, and
decrease-key must land inside heap order — checked by a walk over
raw links, never assumed. Decrease-key targets are tracked by the
Handle push hands back. Runnable in a fresh checkout:
`{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import expose, naive_min, naive_sort
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_items,
    synthetic,
    write_items,
)
from .heap import FibonacciHeap, Handle, HeapError, degree_bound
from .keys import MAX_KEY, KeysError, ensure_key

FIXTURE = "cascading cut pays the debt"
CORPORA = ((1, 2, 3, 4, 5), (5, 3, 8, 1, 4, 9, 2), (-7, 0, 7), tuple(range(64)))


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
    report.section("the pop sequence is the plain sort, exactly")
    for keys in CORPORA:
        heap = FibonacciHeap(keys)
        report.equal(f"{keys[:3]}... peeks the min", heap.peek(), min(keys))
        drained = [heap.pop_min() for _ in range(len(heap))]
        report.equal(f"{len(keys)} items drain to the sort", drained, naive_sort(keys))
        report.ok(f"{len(keys)} items audit clean", heap.invariant())
    corpus = synthetic(40, seed=17)
    heap = FibonacciHeap(corpus)
    report.equal("the raw walk is the sort", expose(heap), naive_sort(corpus))
    report.equal("the min is the plain min", heap.peek(), naive_min(corpus))


def _debt(report: Report) -> None:
    report.section("decrease-key lands inside heap order, tracked by handle")
    for keys in ((40, 30, 20, 10), (5, 6, 7), tuple(range(32))):
        heap = FibonacciHeap()
        ledger: dict[int, int] = {}
        handles: dict[int, Handle] = {}
        for key in keys:
            handle = heap.push(key)
            ledger[handle.token] = key
            handles[handle.token] = handle
        for token, key in list(ledger.items()):
            heap.decrease(handles[token], key - 1000)
            ledger[token] -= 1000
        report.equal(
            f"a decreased heap still walks the sort ({len(keys)} keys)",
            heap.keys(),
            sorted(ledger.values()),
        )
        report.ok(f"a decreased heap audits clean ({len(keys)} keys)", heap.invariant())
    small = FibonacciHeap([9, 8, 7])
    handle = next(iter(small._handles.values()))
    report.refuses(
        "an increase is refused by name",
        lambda: small.decrease(handle, 999),
        HeapError,
    )
    report.equal("the refused increase changed nothing", small.keys(), [7, 8, 9])
    stale = FibonacciHeap([1])
    token = stale.push(2)
    stale.pop_min()
    stale.pop_min()
    report.refuses("a stale handle is refused", lambda: stale.decrease(token, 0), HeapError)


def _ceiling(report: Report) -> None:
    report.section("every degree stays under the documented bound")
    report.equal("the bound of zero items", degree_bound(0), 0)
    report.equal("the bound of two items", degree_bound(2), 4)
    for count in (10, 64, 256):
        heap = FibonacciHeap(synthetic(count, seed=count))
        for _ in range(count // 2):
            heap.pop_min()
        bound = degree_bound(max(len(heap), 1))
        report.ok(
            f"{count} items keep degrees under {bound}",
            all(degree <= bound for degree in heap.degrees()),
        )
    rising = FibonacciHeap(range(1, 200))
    rising_drained = [rising.pop_min() for _ in range(len(rising))]
    report.equal("rising pushes drain sorted", rising_drained, list(range(1, 200)))


def _edges(report: Report) -> None:
    report.section("empty, single, and duplicated items answer quietly")
    bare = FibonacciHeap()
    report.equal("the empty heap keys empty", bare.keys(), [])
    report.equal("the empty heap is size zero", len(bare), 0)
    report.ok("the empty heap is seated", bare.invariant())
    report.refuses("an empty peek is refused", bare.peek, HeapError)
    report.refuses("an empty pop is refused", bare.pop_min, HeapError)
    one = FibonacciHeap([7])
    report.equal("one item peeks itself", one.peek(), 7)
    report.equal("one item pops itself", one.pop_min(), 7)
    report.equal("one item drains to empty", len(one), 0)
    dup = FibonacciHeap([1, 1, 1])
    report.equal("a duplicated key sits three times", len(dup), 3)
    report.equal("a duplicated key drains sorted", dup.keys(), [1, 1, 1])


def _corpora(report: Report) -> None:
    report.section("the item list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the keys are distinct", len(set(corpus)) == 20)
    report.refuses("no items from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its keys", list(thawed.keys), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/items.txt"
        write_items(corpus, path)
        report.equal("a written list reads back", load_items(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_items(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7.5\n")
        report.refuses("a noisy list is refused", lambda: load_items(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every move")
    from .workload import (
        WorkloadError,
        decrease_holds,
        replay_matches,
        run_storm,
    )

    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.ok(f"the storm drained to the sort (seed {seed})", storm.exact)
        report.ok(
            f"the storm checked more than it stepped (seed {seed})",
            storm.checks > storm.steps,
        )
        report.ok(f"the storm decreased something (seed {seed})", storm.decreases > 0)
    report.ok("a quiet heap replays the sort", replay_matches([9, 40, -3]))
    report.ok("a decreased forest stays ordered", decrease_holds([8, 4, 6], 1, -2))
    report.ok(
        "an increase is not a decrease",
        not decrease_holds([8, 4, 6], 0, 99),
    )
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), WorkloadError
    )


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import heap as heap_module

    report.ok(
        "the marker the detector looks for is in the heap module",
        FIXTURE in " ".join((heap_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _order(report)
    _debt(report)
    _ceiling(report)
    _edges(report)
    _corpora(report)
    _storms(report)
    _stories(report)
    return report
