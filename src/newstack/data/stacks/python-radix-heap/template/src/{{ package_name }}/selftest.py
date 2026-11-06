"""The invariants this heap promises, run against the real modules.

Every claim here is the reason the buckets can be trusted: pop-min must
drain exactly the sorted corpus on monotone and mixed streams, every
held key must sit at its bit-length-from-base bucket after every op,
and a backwards push must cost exactly one rebuild, never a wrong
answer. Runnable in a fresh checkout: `{{ package_name }} selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .heap import HeapError, RadixHeap, bucket_of
from .keys import KeyValueError, describe, ensure_key
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_keys,
    monotone,
    synthetic,
    write_keys,
)
from .workload import WorkloadError, run_monotone, run_workload

FIXTURE = "buckets follow the bits"
KEYS = [0, 4, 15, 17, 30, 63, 64, 100, 255, 256, 500, 900, 1023, 2047, 4095]


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


def _seats(report: Report) -> None:
    report.section("a seat is a bit-length, not a comparison")
    report.equal("zero sits at the base", bucket_of(0, 0), 0)
    report.equal("eight differs from zero in four bits", bucket_of(8, 0), 4)
    report.equal("sixty-three differs from sixty-four in seven bits", bucket_of(63, 64), 7)
    report.equal("a key at the base seats itself", bucket_of(17, 17), 0)
    report.refuses(
        "a key below the floor is refused", lambda: RadixHeap().push(-1), HeapError
    )
    report.refuses(
        "a sixty-six-bit key has no bucket",
        lambda: RadixHeap().push((1 << 65) + 7),
        HeapError,
    )


def _drain(report: Report) -> None:
    report.section("pop-min answers sorted, on any stream")
    heap = RadixHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
    report.equal("the count is the count", len(heap), len(KEYS))
    report.equal("draining is the sorted corpus", list(heap.pop_all()), sorted(KEYS))
    report.ok("a drained heap holds nothing", not heap)
    report.refuses("an empty heap refuses to pop", lambda: RadixHeap().pop(), HeapError)
    mixed = RadixHeap()
    for key, value in synthetic(120, seed=17):
        mixed.push(key, value)
    report.equal("a shuffled corpus drains sorted", list(mixed.pop_all()),
                 sorted(key for key, _ in synthetic(120, seed=17)))
    report.ok("the answer is exact, not close", mixed.rebuilds == 0)


def _seating(report: Report) -> None:
    report.section("every key sits at its bit-length-from-base bucket")
    heap = RadixHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
        report.ok(f"seated {key} at its bits", heap.invariant())
        seat = next(i for i, bucket in enumerate(heap._buckets)
                    if any(held == key for held, _ in bucket))
        report.equal(f"{key} seats where its bits say", seat, bucket_of(key, heap.base))
    for _ in range(5):
        heap.pop()
        report.ok("seating survives a pop", heap.invariant())
    report.equal("the base walked to the fifth key", heap.base, sorted(KEYS)[4])
    ahead = [key for key, _ in heap.entries()]
    report.ok("no survivor hides below the base", all(key >= heap.base for key in ahead))


def _backwards(report: Report) -> None:
    report.section("a backwards push buys one rebuild, never a wrong answer")
    heap = RadixHeap()
    for key in (5, 9, 14):
        heap.push(key, None)
    heap.pop()
    before = heap.rebuilds
    edit = heap.push(3, "three")
    report.ok("the push names itself a rebuild", edit.rebuilt)
    report.equal("exactly one rebuild was spent", heap.rebuilds, before + 1)
    report.ok("the heap is seated again", heap.invariant())
    report.equal("the answer survived the rebuild", list(heap.pop_all()), [3, 9, 14])


def _streams(report: Report) -> None:
    report.section("the stream in and the snapshot out")
    pairs = synthetic(60, seed=5)
    report.equal("the generator is deterministic", pairs, synthetic(60, seed=5))
    report.ok("the keys are distinct", len({key for key, _ in pairs}) == 60)
    report.refuses("a corpus of zero is no corpus", lambda: synthetic(0), StreamError)
    rising = monotone(32, seed=4)
    report.equal("the monotone stream rises", [key for key, _ in rising],
                 sorted(key for key, _ in rising))
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


def _keys(report: Report) -> None:
    report.section("the window walks whole numbers")
    report.equal("the key comes back itself", ensure_key(7), 7)
    report.equal("a key renders as itself", describe(42), "42")
    report.refuses("a list has no bucket", lambda: ensure_key([1]), KeyValueError)
    report.refuses("a flag is no key", lambda: ensure_key(True), KeyValueError)


def _storms(report: Report) -> None:
    report.section("the storms, replayed against the sorted truth")
    storm = run_workload(seed=13)
    report.equal("the mixed storm ran its steps", storm.steps, 160)
    report.equal("the mixed storm broke no invariant", storm.breaks, 0)
    report.ok("the mixed storm answered sorted", storm.sorted_held)
    report.ok("the storm checked more than it stepped", storm.checks > storm.steps)
    forward = run_monotone(seed=11, size=64)
    report.equal("a monotone stream spends no rebuild", forward.rebuilds, 0)
    report.equal("a monotone stream breaks nothing", forward.breaks, 0)
    report.ok("a monotone stream answers sorted", forward.sorted_held)
    report.refuses(
        "a storm outside its bounds is refused",
        lambda: run_workload(steps=0),
        WorkloadError,
    )


def _window(report: Report) -> None:
    report.section("the window never walks back on its own")
    heap = RadixHeap()
    for key in KEYS:
        heap.push(key, None)
    walked = [heap.pop()[0] for _ in range(6)]
    report.equal("six pops are six ascending keys", walked, sorted(walked))
    report.ok("the window stands under every held key", all(
        key >= heap.base for key, _ in heap.entries()
    ))
    heap.rebuild()
    report.ok("a rebuild re-seats every key", heap.invariant())
    report.equal("a rebuild loses nothing", len(heap), len(KEYS) - 6)
    report.equal("the rebuilt answer is still sorted",
                 list(heap.pop_all()), sorted(KEYS)[6:])


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
    _seats(report)
    _drain(report)
    _seating(report)
    _backwards(report)
    _keys(report)
    _streams(report)
    _storms(report)
    _window(report)
    _stories(report)
    return report
