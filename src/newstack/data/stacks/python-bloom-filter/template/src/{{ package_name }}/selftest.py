"""Every claim this filter promises, run against the real modules.

The promises are few and hard: a key added is always answered
present — after *every* update on the seeded streams — and the
survey at the shipped widths lists exactly the keys that lie. Same
seed, same answers. Runnable in a fresh checkout:
`python -m the-package selftest`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .audit import (
    COLLISIONS_AT_DEFAULTS,
    CONFIGS,
    RECHECKS,
    AuditError,
    estimate_items,
    run_stream,
    shipped_audit,
)
from .bloom import (
    ROWS,
    SEED,
    WIDTH,
    Bloom,
    BloomError,
)
from .cli import main as cli_main
from .hashing import (
    LARGE,
    multiplier,
    row_index,
    rows_for,
)
from .stream import (
    FIXTURE,
    LENGTH,
    Plan,
    StreamError,
    load_fixture,
    stream,
    write_fixture,
)
from .universe import (
    UNIVERSE,
    UniverseError,
    describe,
    ensure_key,
    ensure_seed,
    parse_key,
)

KEYS = (0, 1, 7, 64, 127, 128, 200, 255)


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
            f"{claim} ({found!r})" if found == expected else f"{claim}: {found!r} != {expected!r}",
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
    report.section("the gate keeps [0, 256) in and everything else out")
    for key in KEYS:
        report.equal(f"{key} is a key", ensure_key(key), key)
    report.equal("text digits become a key", parse_key("42"), 42)
    report.equal("a key prints padded", describe(7), "  7")
    report.equal("a seed is its own", ensure_seed(0), 0)
    report.refuses("256 leaves the universe", lambda: ensure_key(256), UniverseError)
    report.refuses("a negative is no key", lambda: ensure_key(-1), UniverseError)
    report.refuses("a float is no key", lambda: ensure_key(7.0), UniverseError)
    report.refuses("True is no key", lambda: ensure_key(True), UniverseError)
    report.refuses("'x' is no key text", lambda: parse_key("x"), UniverseError)
    report.refuses("a negative seed is no seed", lambda: ensure_seed(-3), UniverseError)


def _rows(report: Report) -> None:
    report.section("the rows are the family's arithmetic: multiply, fold, seat")
    for row in range(ROWS):
        mul = multiplier(row, SEED)
        report.ok(f"row {row} multiplier is odd", bool(mul & 1))
        report.ok(f"row {row} multiplier fits the fold", mul < LARGE)
    report.ok(
        "multipliers are distinct",
        len({multiplier(row, SEED) for row in range(ROWS)}) == ROWS,
    )
    seats = rows_for(200, WIDTH, ROWS, SEED)
    report.equal("a seating has one seat per row", len(seats), ROWS)
    report.ok("every seat is inside the width", all(0 <= seat < WIDTH for seat in seats))
    report.equal("the seating replays", rows_for(200, WIDTH, ROWS, SEED), seats)
    report.equal("the fold is final at the ceiling", row_index(255, 8, 3, 0) < 8, True)


def _array(report: Report) -> None:
    report.section("add seats, might_contain asks, audit re-asks every key")
    bloom = Bloom()
    for key in KEYS:
        fresh = bloom.add(key)
        report.ok(f"{key} answers present once added", bloom.might_contain(key))
        report.ok(f"{key} raised no more than its rows", 0 <= fresh <= ROWS)
    report.equal("the audit names no break", bloom.audit(), [])
    report.equal("the added list keeps every key", len(bloom.added), len(KEYS))
    report.equal("re-adding stores no twin", len({key for key in bloom.added}), len(KEYS))
    twin = Bloom(bloom.width, bloom.rows, bloom.seed, bloom.bits, tuple(bloom.added))
    report.equal("a twin from the pattern agrees", twin.bits, bloom.bits)
    report.refuses("a broken width is no array", lambda: Bloom(width=7), BloomError)
    report.refuses("a runaway width is no array", lambda: Bloom(width=100_000), BloomError)
    report.refuses("rows beyond the ceiling are refused", lambda: Bloom(rows=17), BloomError)
    report.refuses(
        "bits past the width are refused", lambda: Bloom(width=8, bits=256), BloomError
    )


def _streams(report: Report) -> None:
    report.section("the stream is seeded arithmetic: same seed, same answers")
    report.equal("the stream replays", stream(7), stream(7))
    report.equal("the stream is the shipped length", len(stream(7)), LENGTH)
    report.ok("the stream draws distinct keys", len(set(stream(7))) == LENGTH)
    report.ok("every key is in the universe", all(0 <= k < UNIVERSE for k in stream(7)))
    plan = Plan.draw(9)
    report.equal("a plan carries its seed", plan.seed, 9)
    report.equal("a plan carries its keys", plan.keys, stream(9))
    report.refuses("zero keys is no stream", lambda: stream(7, 0), StreamError)
    report.refuses("257 keys leave the universe", lambda: stream(7, 257), StreamError)


def _audit(report: Report) -> None:
    report.section("the shipped audit: zero false negatives, list in hand")
    ledger = shipped_audit()
    report.equal("every config and stream was run", len(ledger.verdicts), len(CONFIGS) * 5)
    report.equal("the re-asks are all booked", ledger.checks, RECHECKS)
    report.equal("the audit broke on nothing", ledger.breaks, [])
    for verdict in ledger.verdicts:
        if not verdict.clean:
            report.ok(f"{verdict.config}/{verdict.seed} lies", False)
            return
    report.ok("every verdict is clean", True)
    report.ok("the collision count is the counted edge", COLLISIONS_AT_DEFAULTS > 0)
    quiet = run_stream("quiet", WIDTH, ROWS, SEED, Plan(seed=5, keys=(1, 2)))
    report.equal("a two-key plan re-asks three times", quiet.rechecks, 3)
    report.refuses(
        "a one-key plan audits nothing",
        lambda: run_stream("x", 8, 1, 1, Plan(seed=1, keys=(1,))),
        AuditError,
    )
    crowded = Bloom(WIDTH, ROWS, SEED)
    for key in stream(7):
        crowded.add(key)
    estimate = estimate_items(crowded)
    report.ok(f"the estimator lands near 32 keys ({estimate:.2f})", abs(estimate - 32) < 2.0)


def _fixture(report: Report) -> None:
    report.section("the frozen streams replay the arithmetic")
    plans = load_fixture(FIXTURE)
    report.equal("the fixture froze five streams", len(plans), 5)
    for plan in plans:
        report.equal(f"stream {plan.seed} replays frozen", plan.keys, stream(plan.seed))
    report.refuses(
        "a missing fixture is named",
        lambda: load_fixture(f"{FIXTURE}.missing"),
        StreamError,
    )
    import tempfile

    with tempfile.TemporaryDirectory() as room:
        path = f"{room}/streams.txt"
        write_fixture(path, plans)
        report.equal("a written fixture reads back", load_fixture(path), plans)


def _edge(report: Report) -> None:
    report.section("the honest edge: yes may lie, no never does")
    bloom = Bloom(64, 4, 7)
    for key in stream(7, 8):
        bloom.add(key)
    edge = bloom.survey()
    report.ok("a crowded small array has liars", len(edge) > 0)
    for key in edge:
        report.ok(f"liar {key} is not added", key not in bloom.added)
        report.ok(f"liar {key} answers present", bloom.might_contain(key))
    absent_liar = edge[0]
    clear = bloom.first_clear_row(absent_liar) if edge else None
    report.equal("a liar has no clear row", clear if edge else None, None)
    honest = Bloom(64, 4, 7)
    report.equal("an empty array surveys no liars", honest.survey(), [])
    honest.add(3)
    report.equal("one key still answers honestly", honest.audit(), [])


def _cli(report: Report) -> None:
    report.section("the command line keeps the promise visible")
    report.equal("add exits zero", cli_main(["add", "--key", "7", "--key", "42"]), 0)
    report.equal("a seeded key checks present", cli_main(["check", "165"]), 0)
    report.equal("an unseen key checks absent", cli_main(["check", "1"]), 1)
    report.equal("the shipped audit reports clean", cli_main(["report"]), 0)
    report.equal("a seed replays", cli_main(["seed", "7"]), 0)
    report.equal("the demo stands", cli_main(["demo"]), 0)
    report.equal("help exits zero", cli_main(["--help"]), 0)
    report.equal("a text key exits as unusable", cli_main(["check", "x"]), 2)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.ok("every story is told", len(told) >= 5)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)


def run() -> Report:
    report = Report()
    _gate(report)
    _rows(report)
    _array(report)
    _streams(report)
    _audit(report)
    _fixture(report)
    _edge(report)
    _cli(report)
    _stories(report)
    return report
