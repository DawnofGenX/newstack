"""The invariants this buffer promises, run against the real modules.

Every claim here is the reason the values can be trusted: on seeded
push/pop storms the drain must equal the reference deque EXACTLY
under the drop-oldest rule, the cursor must never land outside
`[0, capacity)`, a full buffer's oldest must be exactly the next
overwrite, and capacity-one and empty edges must stay honest. The
walk that recomputes contents from `(head, count)` must equal the
visible sequence after every operation. Runnable in a fresh checkout:
`{{ package_name }} selftest`.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import reference_drain
from .corpus import DEFAULT_SEED, CorpusError, Snapshot, load_values, synthetic
from .ring import RingBuffer, RingError
from .storm import StormError, drain_matches, run_storm, storm_matches
from .values import MAX_VALUE, ValuesError, ensure_value

FIXTURE = "the cursor never leaves the ring"
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
    report.equal("a value comes back itself", ensure_value(-42), -42)
    report.equal("the largest value passes", ensure_value(MAX_VALUE), MAX_VALUE)
    report.refuses("a float is no value", lambda: ensure_value(1.5), ValuesError)
    report.refuses("a string is no value", lambda: ensure_value("7"), ValuesError)
    report.refuses("a bool is no value", lambda: ensure_value(True), ValuesError)
    report.refuses(
        "one past the ceiling is no value", lambda: ensure_value(MAX_VALUE + 1), ValuesError
    )
    report.refuses("a zero-capacity ring is refused", lambda: RingBuffer(0), RingError)


def _drain(report: Report) -> None:
    report.section("the drain is the reference deque, exactly")
    for keys in CORPORA:
        for capacity in (1, 3, 8):
            ring = RingBuffer(capacity, list(keys))
            report.equal(
                f"{capacity} slots drain the deque of {len(keys)} pushes",
                list(ring.drain()),
                reference_drain(capacity, list(keys)),
            )
    corpus = synthetic(40, seed=17)
    report.ok(
        "forty pushes drain the deque",
        drain_matches(8, corpus) and drain_matches(64, corpus),
    )


def _cursor(report: Report) -> None:
    report.section("the cursor never lands outside [0, capacity)")
    for capacity in (1, 2, 7, 16):
        ring = RingBuffer(capacity)
        clean = True
        for step in range(capacity * 5):
            ring.push(step)
            if not ring.invariant():
                clean = False
                break
            if step % 3:
                with contextlib.suppress(RingError):
                    ring.pop()
                if not ring.invariant():
                    clean = False
                    break
        report.ok(f"{capacity} slots hold the cursor for {capacity * 5} moves", clean)


def _oldest(report: Report) -> None:
    report.section("a full ring overwrites exactly the oldest")
    for capacity in (1, 4, 9):
        ring = RingBuffer(capacity, range(capacity))
        oldest = ring.peek()
        dropped = ring.push(999)
        report.equal(f"{capacity} slots drop exactly the oldest", dropped, oldest)
        report.equal(
            "the write landed on the oldest slot",
            ring.contents()[-1],
            999,
        )
        report.ok("the audit is clean after the drop", not ring.audit())


def _edges(report: Report) -> None:
    report.section("empty, capacity-one, and drained edges answer quietly")
    bare = RingBuffer(4)
    report.equal("the empty buffer counts zero", len(bare), 0)
    report.equal("the empty buffer walks empty", bare.contents(), ())
    report.refuses("an empty pop is refused", lambda: bare.pop(), RingError)
    report.refuses("an empty peek is refused", lambda: bare.peek(), RingError)
    report.equal("a refused pop changed nothing", len(bare), 0)
    lone = RingBuffer(1, [7, 8, 9])
    report.equal("capacity one keeps the newest", lone.peek(), 9)
    report.equal("capacity one overwrote twice", lone.overwrites, 2)
    report.equal("capacity one drains the newest", lone.drain(), [9])
    report.equal("a drained buffer parks at zero", (lone.head, len(lone)), (0, 0))


def _walk(report: Report) -> None:
    report.section("the walk from (head, count) equals the visible sequence")
    for capacity in (3, 8):
        ring = RingBuffer(capacity)
        seats: list[int] = []
        clean = True
        for step in range(capacity * 6):
            if ring.push(step) is not None:
                seats.pop(0)
            seats.append(step)
            if list(ring.contents()) != seats:
                clean = False
                break
            if step % 2 and seats and ring.pop() != seats.pop(0):
                clean = False
                break
        report.ok(f"{capacity} slots walk the visible sequence", clean)


def _corpora(report: Report) -> None:
    report.section("the value list in, the snapshot out")
    corpus = synthetic(20, seed=5)
    report.equal("the generator is deterministic", corpus, synthetic(20, seed=5))
    report.ok("the values are distinct", len(set(corpus)) == 20)
    report.refuses("no values from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its values", list(thawed.values), corpus)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/values.txt"
        from .corpus import write_values

        write_values(corpus, path)
        report.equal("a written list reads back", load_values(path), corpus)
        report.refuses(
            "a missing list is named", lambda: load_values(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7.5\n")
        report.refuses("a noisy list is refused", lambda: load_values(noise), CorpusError)


def _storms(report: Report) -> None:
    report.section("the storm, re-checked after every move")
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        report.equal(f"the storm ran its steps (seed {seed})", storm.steps, 140)
        report.equal(f"the storm broke nothing (seed {seed})", storm.breaks, 0)
        report.ok(f"the storm stayed seated (seed {seed})", storm.seated)
        report.ok(
            f"the storm checked more than it stepped (seed {seed})",
            storm.checks > storm.steps,
        )
    for capacity in (1, 5, 16):
        report.ok(f"the ring answers like the deque at {capacity} slots",
                  storm_matches(capacity, 4242))
    report.refuses(
        "a storm without steps is refused", lambda: run_storm(steps=0), StormError
    )


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import ring as ring_module

    report.ok(
        "the marker the detector looks for is in the ring module",
        FIXTURE in " ".join((ring_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _drain(report)
    _cursor(report)
    _oldest(report)
    _edges(report)
    _walk(report)
    _corpora(report)
    _storms(report)
    _stories(report)
    return report
