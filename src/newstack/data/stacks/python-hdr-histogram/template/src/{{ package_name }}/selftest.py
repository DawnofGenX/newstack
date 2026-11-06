"""In-process checks: the layout, the promise, the merge, and the command line."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from . import cli as cli_module
from . import demo as demo_module
from .histogram import (
    Histogram,
    HistogramError,
    ceiling_of,
    floor_of,
    index_of,
    parse_histogram,
    relative_error,
    width_of,
)
from .stats import StatsError, average_of_percentiles, check, nearest_rank


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
    values = [0, 1, 1023, 1024, 2047, 2048, 4095, 1_000_000]
    report.ok(
        "every index is monotone in the value",
        [index_of(value) for value in values] == sorted(index_of(value) for value in values),
    )
    report.ok("a value below the first bucket is exact", width_of(index_of(1023)) == 1)
    report.ok("the first bucket above is still exact", width_of(index_of(2047)) == 1)
    report.ok("the next bucket is two values wide", width_of(index_of(2048)) == 2)
    report.ok("index_of and floor_of agree at the bucket floor", floor_of(index_of(2048)) == 2048)
    report.ok(
        "the ceiling covers the value",
        ceiling_of(index_of(4095)) >= 4095,
    )
    report.ok(
        "the promised error is one part in a thousand",
        abs(relative_error(10) - 1 / 1024) < 1e-15,
    )
    report.ok("fourteen bits promise less error than ten", relative_error(14) < relative_error(10))
    report.refuses(
        "zero significant bits are refused",
        HistogramError,
        lambda: Histogram(0),
    )
    report.refuses(
        "a negative latency is refused",
        HistogramError,
        lambda: Histogram().record(-1),
    )
    report.refuses(
        "a float latency is refused",
        HistogramError,
        lambda: Histogram().record(1.5),  # type: ignore[arg-type]
    )
    report.refuses(
        "a value past the layout is refused",
        HistogramError,
        lambda: Histogram(10, max_value=1000).record(10_000),
    )


def _promise(report: Report) -> None:
    values = [10, 20, 30, 40, 50, 100, 200, 400, 800, 1_600, 3_200, 6_400]
    histogram = Histogram(10)
    histogram.record_many(values)
    compared = check(histogram, values, points=(50.0, 90.0, 100.0))
    report.ok("the check holds for a small sample", compared.held())
    report.ok(
        "a reported percentile is never below the truth",
        all(row.reported >= row.truth for row in compared.rows),
    )
    report.ok(
        "the largest sample is reported at least as large", histogram.percentile(100.0) >= 6_400
    )
    report.ok("the count is exact", histogram.count() == len(values))
    report.ok("the mean is exact", abs(histogram.mean() - sum(values) / len(values)) < 1e-9)
    report.ok("the sum is exact", histogram.total_sum == sum(values))
    report.refuses(
        "a percentile of nothing is refused",
        HistogramError,
        lambda: Histogram().percentile(50.0),
    )
    report.refuses(
        "a percentile of zero is refused",
        HistogramError,
        lambda: histogram.percentile(0.0),
    )
    report.refuses(
        "a percentile above one hundred is refused",
        HistogramError,
        lambda: histogram.percentile(100.5),
    )
    report.refuses(
        "nearest_rank of nothing is refused",
        StatsError,
        lambda: nearest_rank([], 50.0),
    )


def _merge(report: Report) -> None:
    left = Histogram(10)
    right = Histogram(10)
    left.record_many(range(1, 100))
    right.record_many(range(100, 200))
    merged = left.merged(right)
    whole = Histogram(10)
    whole.record_many(range(1, 200))
    report.ok("the merged count adds up", merged.count() == 199)
    report.ok(
        "the merged buckets match one pass", merged.as_dict()["counts"] == whole.as_dict()["counts"]
    )
    report.ok(
        "merging with an empty histogram changes nothing", left.merged(Histogram(10)).count() == 99
    )
    report.ok("a merge keeps the lowest value", merged.lowest == 1)
    report.refuses(
        "a merge across layouts is refused",
        HistogramError,
        lambda: left.merged(Histogram(12)),
    )


def _average_trap(report: Report) -> None:
    report.ok(
        "the average of one percentile is that percentile",
        abs(average_of_percentiles([{"p95": 10.0}], "p95") - 10.0) < 1e-9,
    )
    report.refuses(
        "averaging no groups is refused",
        StatsError,
        lambda: average_of_percentiles([], "p95"),
    )


def _serialisation(report: Report) -> None:
    histogram = Histogram(10)
    histogram.record_many([1, 2, 3, 1024, 5000])
    payload = histogram.as_dict()
    again = parse_histogram(payload)
    report.ok("a histogram round trips through its dictionary", again.as_dict() == payload)
    report.ok("the round trip keeps the count", again.count() == histogram.count())
    report.refuses(
        "a foreign dictionary is refused",
        HistogramError,
        lambda: parse_histogram({"type": "sketch"}),
    )
    report.refuses(
        "a dictionary without counters is still readable",
        HistogramError,
        lambda: parse_histogram({"type": "hdr-histogram", "significant_bits": 10, "counts": "x"}),
    )


def _stories(report: Report) -> None:
    lines, held = demo_module.render_stories()
    report.ok("every story holds", held, "one of the stories is broken")
    report.ok("all six stories ran", len(demo_module.stories()) == 6)
    report.ok("the stories print a verdict line each", lines.count("  -> holds") == 6)
    report.ok("the run ends with a summary", lines[-1] == "stories      6 of 6 hold")


def _command_line(report: Report) -> None:
    parser = cli_module.build_parser()
    report.ok(
        "the parser routes selftest without running it",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    report.ok(
        "the parser routes demo",
        parser.parse_args(["demo"]).handler is cli_module._command_demo,
    )
    fixture = Path(__file__).resolve().parent.parent.parent / "fixtures" / "latencies.jsonl"
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        code = cli_module.main(["percentile", "--input", str(fixture), "--p", "50,99"])
    report.ok("a percentile run on the fixture exits zero", code == 0)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        unknown = cli_module.main(["percentile", "--input", "/nonexistent/latencies.jsonl"])
    report.ok("a missing file is a usage error", unknown == 2)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        no_command = cli_module.main([])
    report.ok("no command prints help and exits two", no_command == 2)


def main() -> int:
    report = Report()
    for section in (
        _layout,
        _promise,
        _merge,
        _average_trap,
        _serialisation,
        _stories,
        _command_line,
    ):
        section(report)
    print(f"selftest: {report.passed} checks passed, {report.failed} failed")
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
