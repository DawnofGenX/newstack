"""The invariants this sketch promises, run against the real modules.

Every claim here is the reason the counts can be trusted: the min of
rows never dips under the ledger truth (the audit runs after every
update, never assumed), an empty sketch counts zero, the same stream
and seed replay identically, and the shipped grid — bijection rows
over a universe it can seat alone — answers the shipped corpora
exactly. Runnable in a fresh checkout: `python -m the-package
selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .brute import min_of_rows, true_counts
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_stream,
    synthetic,
    write_stream,
)
from .hashes import DEPTH, MULTIPLIERS, WIDTH, bijective, cell_of
from .keys import MAX_KEY, UNIVERSE, KeysError, ensure_key
from .sketch import CountMinSketch

FIXTURE = "the min of rows never dips under the truth"
FIXTURE_STREAM = "fixtures/stream.txt"
KEYSETS = ((0, 1, 2, 3, 4), (7, 64, 128, 199, 255), (0, 85, 170), tuple(range(64)))


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


def _seat(events: list[tuple[int, int]], **shape: object) -> CountMinSketch:
    sketch = CountMinSketch(**shape)  # type: ignore[arg-type]
    for key, n in events:
        sketch.add(key, n)
    return sketch


def _gate(report: Report) -> None:
    report.section("the gate keeps the universe in and noise out")
    report.equal("a key comes back itself", ensure_key(199), 199)
    report.equal("the top of the universe passes", ensure_key(MAX_KEY), MAX_KEY)
    report.refuses("a negative is no key", lambda: ensure_key(-1), KeysError)
    report.refuses("one past the universe is no key", lambda: ensure_key(UNIVERSE), KeysError)
    report.refuses("a float is no key", lambda: ensure_key(1.5), KeysError)
    report.refuses("a string is no key", lambda: ensure_key("7"), KeysError)
    report.refuses("a bool is no key", lambda: ensure_key(True), KeysError)


def _rows(report: Report) -> None:
    report.section("every row is a bijection, same key same cell forever")
    report.ok("the shipped grid is bijective", bijective(WIDTH, MULTIPLIERS))
    report.ok("every row permutes the cells", all(
        sorted(cell_of(key, row, MULTIPLIERS, WIDTH) for key in range(WIDTH))
        == list(range(WIDTH))
        for row in range(DEPTH)
    ))
    report.equal(
        "a cell replays itself",
        cell_of(42, 2, MULTIPLIERS, WIDTH),
        cell_of(42, 2, MULTIPLIERS, WIDTH),
    )
    report.ok("rows are distinct permutations", len(
        {tuple(cell_of(key, row, MULTIPLIERS, WIDTH) for key in range(UNIVERSE))
         for row in range(DEPTH)}
    ) == DEPTH)


def _never_under(report: Report) -> None:
    report.section("the min of rows never dips under the truth")
    for seed in (13, 77):
        sketch = _seat(synthetic(120, seed=seed))
        truth = true_counts(synthetic(120, seed=seed))
        report.ok(f"a seeded stream never undercounted (seed {seed})", all(
            sketch.count(key) >= exact for key, exact in truth.items()
        ))
        report.equal(f"the audit found no break (seed {seed})", sketch.audit(), [])


def _exact(report: Report) -> None:
    report.section("the shipped grid answers the shipped stream exactly")
    for keys in KEYSETS:
        events = [(key, 1 + key % 3) for key in keys]
        sketch = _seat(events)
        truth = true_counts(events)
        for key, exact in truth.items():
            if sketch.count(key) != exact:
                report.equal(f"a seated key answered exactly ({key})", sketch.count(key), exact)
                return
        report.ok(f"{len(keys)} keys answered the ledger exactly", True)


def _empty(report: Report) -> None:
    report.section("an empty sketch counts zero for every key")
    bare = CountMinSketch()
    report.equal("count on a fresh grid", bare.count(7), 0)
    report.equal("a fresh grid audits clean", bare.audit(), [])
    report.equal("a fresh grid tracks nothing", bare.keys(), [])
    report.equal("an empty ledger totals zero", bare.total, 0)


def _deterministic(report: Report) -> None:
    report.section("same seed, same answers, forever")
    for seed in (5, 31):
        first = _seat(synthetic(80, seed=seed))
        second = _seat(synthetic(80, seed=seed))
        report.ok(f"a replay matched its twin (seed {seed})", all(
            first.count(key) == second.count(key) for key in first
        ))
        report.equal(f"the generators agree (seed {seed})",
                     synthetic(80, seed=seed), synthetic(80, seed=seed))


def _min_not_max(report: Report) -> None:
    report.section("the answer is the min of the cells, read raw")
    sketch = _seat([(9, 4), (9, 1), (77, 2)])
    cells = sketch.cells_of(9)
    report.equal("count is the min of raw cells", sketch.count(9),
                 min_of_rows(sketch.rows, cells))
    report.ok("the min never exceeds the tallest cell",
              sketch.count(9) <= max(sketch.rows[r][c] for r, c in enumerate(cells)))
    narrow = _seat([(1, 2), (17, 3)], width=48, multipliers=(3, 5, 7, 11, 13))
    report.equal("a drifting grid still answers the min, not the max",
                 narrow.count(1), narrow.true_count(1))
    report.ok("the drifting grid really drifts upward",
              max(narrow.rows[r][c] for r, c in enumerate(narrow.cells_of(1))) >
              narrow.count(1))


def _audit(report: Report) -> None:
    report.section("the audit catches a grid that undercounts")
    sketch = _seat([(11, 3)])
    row, cell = 0, cell_of(11, 0, sketch.multipliers, sketch.width)
    sketch.rows[row][cell] -= 1
    caught = sketch.audit()
    report.ok("a lowered cell is caught", bool(caught))
    sketch.rows[row][cell] += 1
    report.equal("the raised grid audits clean again", sketch.audit(), [])


def _corpora(report: Report) -> None:
    report.section("the stream in, the snapshot out")
    events = synthetic(20, seed=5)
    report.equal("the generator is deterministic", events, synthetic(20, seed=5))
    report.refuses("no events from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(events), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its events", list(thawed.events), events)
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'), CorpusError
    )
    with TemporaryDirectory() as room:
        path = f"{room}/stream.txt"
        write_stream(events, path)
        report.equal("a written stream reads back", load_stream(path), events)
        report.refuses(
            "a missing stream is named", lambda: load_stream(f"{room}/missing.txt"), CorpusError
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n7.5\n")
        report.refuses("a noisy stream is refused", lambda: load_stream(noise), CorpusError)


def _streams(report: Report) -> None:
    from .workload import (
        WorkloadError,
        run_stream,
        stream_matches,
    )

    report.section("the stream, re-audited after every update")
    for seed in (13, 77):
        replay = run_stream(seed=seed)
        report.equal(f"the stream ran its steps (seed {seed})", replay.steps, 140)
        report.equal(f"the stream broke nothing (seed {seed})", replay.breaks, 0)
        report.ok(f"the stream stayed seated (seed {seed})", replay.seated)
        report.ok(
            f"the stream checked more than it stepped (seed {seed})",
            replay.checks > replay.steps,
        )
    report.ok("the shipped shape answers its corpora alike", stream_matches())
    report.refuses(
        "a stream without steps is refused", lambda: run_stream(steps=0), WorkloadError
    )


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import sketch as sketch_module

    report.ok(
        "the marker the detector looks for is in the sketch module",
        FIXTURE in " ".join((sketch_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _rows(report)
    _never_under(report)
    _exact(report)
    _empty(report)
    _deterministic(report)
    _min_not_max(report)
    _audit(report)
    _corpora(report)
    _streams(report)
    _stories(report)
    return report
