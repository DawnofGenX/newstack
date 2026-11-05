"""The console script: read the report, print a summary, optionally gate on duration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import model, selftest

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_OVER = 1
EXIT_UNUSABLE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Summarise the JSON report the plugin wrote."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    summary = commands.add_parser("summary", help="counts, slowest tests, optional duration gate")
    summary.add_argument("report", type=Path)
    summary.add_argument("--top", type=int, default=5, metavar="N")
    summary.add_argument(
        "--fail-over-ms",
        type=float,
        default=None,
        metavar="MS",
        help="exit 1 when any test took longer than MS milliseconds",
    )
    summary.add_argument("--json", action="store_true", help="print the summary as JSON")

    commands.add_parser("selftest", help="check the reader against synthetic reports")
    return parser


def slowest_line(test: model.TestRecord) -> str:
    phase = test.slowest_phase()
    return f"  {test.duration_ms:9.3f} ms  {phase:<8}  {test.nodeid}  [{test.ticket}]"


def count_line(report: model.Report) -> str:
    counts = report.counts()
    parts = [f"{len(report.tests)} tests"]
    parts += [f"{counts[name]} {name}" for name in model.OUTCOMES]
    return "total " + ", ".join(parts)


def summarize(
    report: model.Report, top: int = 5, fail_over_ms: float | None = None
) -> tuple[list[str], int]:
    """Everything except the printing, so a test can assert on lines and status."""
    lines = [count_line(report)]
    if report.tests:
        lines.append("slowest")
        lines.extend(slowest_line(test) for test in report.slowest(top))
    if fail_over_ms is None:
        return lines, EXIT_OK
    over = report.over(fail_over_ms)
    if not over:
        lines.append(f"gate   no test over {fail_over_ms:g} ms")
        return lines, EXIT_OK
    lines.append(f"gate   over {fail_over_ms:g} ms: {len(over)} test(s)")
    lines.extend(f"       {test.duration_ms:9.3f} ms  {test.nodeid}" for test in over)
    return lines, EXIT_OVER


def summary_json(report: model.Report, top: int, fail_over_ms: float | None) -> dict[str, object]:
    return {
        "format": model.FORMAT,
        "exit_status": report.exit_status,
        "tests": len(report.tests),
        "counts": report.counts(),
        "slowest": [
            {
                "nodeid": test.nodeid,
                "duration_ms": test.duration_ms,
                "phase": test.slowest_phase(),
                "ticket": test.ticket,
            }
            for test in report.slowest(top)
        ],
        "over": None
        if fail_over_ms is None
        else [test.nodeid for test in report.over(fail_over_ms)],
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "selftest":
        return selftest.main()
    try:
        report = model.load(args.report)
    except model.InputError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    lines, status = summarize(report, args.top, args.fail_over_ms)
    if args.json:
        print(json.dumps(summary_json(report, args.top, args.fail_over_ms), indent=2))
    else:
        print("\n".join(lines))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
