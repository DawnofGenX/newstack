"""The command line: one run, one report, one honest exit code."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .demo import demo, render
from .engine import Aggregation, Engine, EngineError
from .events import US, EventError, load
from .windows import WindowError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_LATE = 1
EXIT_UNUSABLE = 2

UNITS = {"us": 1, "ms": 1_000, "s": US, "m": 60 * US, "h": 3600 * US, "d": 86400 * US}


def parse_duration(text: str) -> int:
    """`60`, `60s`, `5m`, `1h` → microseconds. A bare number is seconds."""
    stripped = text.strip().lower()
    number, scale = stripped, US
    # Longest suffix first, so "500ms" cannot be read as 500 seconds.
    for suffix in sorted(UNITS, key=len, reverse=True):
        if stripped.endswith(suffix) and stripped[: -len(suffix)]:
            number, scale = stripped[: -len(suffix)], UNITS[suffix]
            break
    try:
        value = float(number)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a duration") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} must be positive")
    return int(value * scale)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Window a time series, and say what arrived too late to count.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="aggregate a JSONL file")
    run.add_argument("--events", required=True, type=Path, help="JSONL of {t, value}")
    run.add_argument("--width", default="60s", type=parse_duration, help="window width")
    run.add_argument("--hop", default=None, type=parse_duration, help="slide (default: width)")
    run.add_argument("--lateness", default="0s", type=parse_duration, help="allowed lateness")
    run.add_argument("--agg", default="count", choices=[member.value for member in Aggregation])
    run.add_argument("--json", default=None, type=Path, help="also write the report here")

    subparsers.add_parser("demo", help="six stories about one minute")
    subparsers.add_parser("selftest", help="run the offline checks")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        for title, lines in demo():
            print(title)
            for line in lines:
                print(f"  {line}")
            print()
        return EXIT_OK
    if args.command == "selftest":
        from .selftest import selftest

        return selftest()
    if args.command != "run":
        parser.print_help()
        return EXIT_UNUSABLE

    try:
        events = load(args.events)
        engine = Engine(
            args.width,
            hop_us=args.hop,
            lateness_us=args.lateness,
            aggregation=args.agg,
        )
        for event in events:
            engine.push(event)
        engine.flush()
        report = engine.report()
    except (EventError, EngineError, WindowError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE

    print(render(report))
    if args.json is not None:
        args.json.write_text(json.dumps(report.as_dict(), indent=2) + "\n")
        print(f"\nwrote {args.json}")

    if report.late:
        # Late data is a data-quality gate, not a footnote: a producer that
        # cannot deliver inside the allowance will keep doing so.
        print(
            f"\n{PROGRAM}: {len(report.late)} event(s) arrived too late to count",
            file=sys.stderr,
        )
        return EXIT_LATE
    return EXIT_OK


def run(argv: list[str] | None = None) -> int:
    return main(argv)
