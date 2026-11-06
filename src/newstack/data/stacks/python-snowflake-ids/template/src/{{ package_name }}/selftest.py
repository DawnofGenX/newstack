"""In-process checks: the layout, the sequence, the clock, and the command line."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

from . import cli as cli_module
from . import demo as demo_module
from .audit import audit, collision, spacing
from .generator import ClockError, ManualClock, SnowflakeGenerator
from .layout import (
    EPOCH_MS,
    IDS_PER_MS,
    MAX_RELATIVE_MS,
    MAX_SEQUENCE,
    MAX_WORKER,
    WORKERS,
    LayoutError,
    compose,
    decode,
    years_of_layout,
)


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok   {name}")
        else:
            self.failed += 1
            print(f"FAIL {name}{': ' + detail if detail else ''}")

    def refuses(self, name: str, kind: type[BaseException], action) -> None:
        try:
            action()
        except kind:
            self.ok(name, True)
        except BaseException as error:
            self.ok(name, False, f"raised {type(error).__name__}: {error}")
        else:
            self.ok(name, False, "nothing was raised")


def _layout(report: Report) -> None:
    value = compose(1_000, 7, 42)
    decoded = decode(value)
    report.ok(
        "compose and decode round trip",
        (decoded.relative_ms, decoded.worker, decoded.sequence) == (1_000, 7, 42),
    )
    report.ok("a worker at zero reads back as zero", decode(compose(5, 0, 0)).worker == 0)
    report.ok("the last worker reads back", decode(compose(5, MAX_WORKER, 0)).worker == MAX_WORKER)
    report.ok(
        "the last sequence reads back", decode(compose(5, 0, MAX_SEQUENCE)).sequence == MAX_SEQUENCE
    )
    report.ok(
        "more milliseconds means a larger identifier",
        compose(2_000, 0, 0) > compose(1_000, MAX_WORKER, MAX_SEQUENCE),
    )
    report.ok("ten bits of worker is 1024", WORKERS == 1_024)
    report.ok("twelve bits of sequence is 4096", IDS_PER_MS == 4_096)
    report.ok("forty-one bits is under seventy years", 69 < years_of_layout() < 70)
    report.ok(
        "the last millisecond still composes",
        compose(MAX_RELATIVE_MS, MAX_WORKER, MAX_SEQUENCE) > 0,
    )
    report.refuses(
        "a worker past the field is refused", LayoutError, lambda: compose(1, MAX_WORKER + 1, 0)
    )
    report.refuses("a negative worker is refused", LayoutError, lambda: compose(1, -1, 0))
    report.refuses(
        "a sequence past the field is refused", LayoutError, lambda: compose(1, 0, MAX_SEQUENCE + 1)
    )
    report.refuses("a negative timestamp is refused", LayoutError, lambda: compose(-1, 0, 0))
    report.refuses(
        "a timestamp past the field is refused",
        LayoutError,
        lambda: compose(MAX_RELATIVE_MS + 1, 0, 0),
    )
    report.refuses("a boolean worker is refused", LayoutError, lambda: compose(1, True, 0))
    report.refuses("a negative identifier is refused", LayoutError, lambda: decode(-1))


def _generator(report: Report) -> None:
    clock = ManualClock(EPOCH_MS)
    worker = SnowflakeGenerator(3, clock=clock)
    first = worker.next_id()
    second = worker.next_id()
    report.ok("two identifiers in one millisecond differ", first != second)
    report.ok("the sequence advances", (decode(first).sequence, decode(second).sequence) == (0, 1))
    clock.advance(1)
    third = worker.next_id()
    report.ok("a new millisecond restarts the sequence", decode(third).sequence == 0)
    report.ok("the millisecond advanced", decode(third).relative_ms == 1)

    clock = ManualClock(EPOCH_MS)
    filler = SnowflakeGenerator(4, clock=clock)
    values = [filler.next_id() for _ in range(IDS_PER_MS + 1)]
    report.ok(
        "the first millisecond holds 4096",
        sum(1 for value in values if decode(value).relative_ms == 0) == IDS_PER_MS,
    )
    report.ok("the overflow waits once", filler.waits == 1)
    report.ok("the overflow lands in the next millisecond", decode(values[-1]).relative_ms == 1)
    report.ok("identifiers stay increasing across the wait", values == sorted(values))
    report.refuses(
        "a bad rollback strategy is refused",
        ClockError,
        lambda: SnowflakeGenerator(1, on_rollback="ignore"),
    )


def _rollback(report: Report) -> None:
    clock = ManualClock(EPOCH_MS + 1_000)
    strict = SnowflakeGenerator(5, clock=clock)
    strict.next_id()
    clock.set(EPOCH_MS + 999)
    report.refuses("a backwards clock is refused by default", ClockError, strict.next_id)

    clock = ManualClock(EPOCH_MS + 1_000)
    holding = SnowflakeGenerator(5, clock=clock, on_rollback="hold")
    holding.next_id()
    clock.set(EPOCH_MS + 990)
    held = [holding.next_id() for _ in range(4)]
    report.ok(
        "holding keeps the last millisecond",
        {decode(value).relative_ms for value in held} == {1_000},
    )
    report.ok(
        "holding spends the sequence", [decode(value).sequence for value in held] == [1, 2, 3, 4]
    )
    report.ok("the holds are counted", holding.holds == 4)

    frozen = demo_module.Frozen(EPOCH_MS + 1_000)
    spender = SnowflakeGenerator(6, clock=frozen, on_rollback="hold")
    spender.next_id()
    frozen.set(EPOCH_MS + 990)
    spent = 0
    try:
        for _ in range(MAX_SEQUENCE + 3):
            spender.next_id()
            spent += 1
    except ClockError:
        pass
    report.ok("the held sequence is finite", spent == MAX_SEQUENCE)


def _audit(report: Report) -> None:
    clock = ManualClock(EPOCH_MS)
    worker = SnowflakeGenerator(9, clock=clock)
    values = []
    for _ in range(6):
        values.append(worker.next_id())
        clock.advance(1)
    result = audit(values)
    report.ok("a clean stream is sound", result.held())
    report.ok("the worker is named", result.workers == (9,))
    report.ok("no duplicates are reported", result.duplicates == 0)
    report.ok("the span counts the milliseconds", result.span_ms == 5)
    report.refuses("an empty stream is refused", LayoutError, lambda: audit([]))
    repeated = audit([*values, values[-1]])
    report.ok("a repeated identifier is a duplicate", repeated.duplicates == 1)
    report.ok("a repeated identifier is out of order", not repeated.monotone)
    left, right = collision(0, 1, relative_ms=10)
    report.ok("two workers differ at the same millisecond", left != right)
    report.ok("spacing finds the smallest gap", spacing([10, 11, 12]) == 1)
    report.refuses("spacing needs two identifiers", LayoutError, lambda: spacing([10]))


def _stories(report: Report) -> None:
    lines, held = demo_module.render_stories()
    report.ok("every story holds", held, "one story is broken")
    report.ok("all six stories ran", len(demo_module.STORIES) == 6)
    report.ok("each story prints a verdict", lines.count("  -> holds") == 6)
    report.ok("the run ends with a summary", lines[-1] == "stories      6 of 6 hold")


def _command_line(report: Report) -> None:
    parser = cli_module.build_parser()
    report.ok(
        "the parser routes selftest",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    report.ok(
        "the parser routes demo", parser.parse_args(["demo"]).handler is cli_module._command_demo
    )
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        code = cli_module.main(["generate", "--count", "3", "--worker", "7", "--spread"])
    report.ok("a generate run exits zero", code == 0)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        bad = cli_module.main(["audit", "--input", "/nonexistent/ids.jsonl"])
    report.ok("a missing file is unusable input", bad == 2)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        nothing = cli_module.main([])
    report.ok("no command prints help and exits two", nothing == 2)


def main() -> int:
    report = Report()
    for section in (_layout, _generator, _rollback, _audit, _stories, _command_line):
        section(report)
    print(f"selftest: {report.passed} checks passed, {report.failed} failed")
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
