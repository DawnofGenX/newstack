"""Report an error budget and page when the burn rate says so."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from . import buckets as buckets_mod
from . import burn, demo
from .slo import SloError, slo_of

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2
DEFAULT_EVENTS = "fixtures/traffic.jsonl"
DEFAULT_TARGET = "99.9"
DEFAULT_WINDOW = "6h"


def _moment(text: str) -> int:
    try:
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise buckets_mod.ReadingError(f"--now {text!r} is not ISO 8601: {error}") from error
    if when.tzinfo is None:
        raise buckets_mod.ReadingError(
            f"--now {text!r} has no offset; the whole point of the window is which "
            "zone its edges are in"
        )
    return int(when.timestamp())


def _add_report_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--events", default=DEFAULT_EVENTS, help="JSON Lines of buckets")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="the SLO, e.g. 99.9")
    parser.add_argument("--window", default=DEFAULT_WINDOW, help="the SLO window, e.g. 30d")
    parser.add_argument("--width", type=int, default=buckets_mod.DEFAULT_WIDTH_S)
    parser.add_argument(
        "--now", help="the right edge of the window; default: after the last bucket"
    )
    parser.add_argument("--json", action="store_true")


def command_report(args: argparse.Namespace) -> int:
    readings = buckets_mod.load(args.events, width_s=args.width)
    slo = slo_of(args.target, args.window)
    now_s = _moment(args.now) if args.now else None
    result = burn.report(readings, slo, now_s=now_s)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        print("\n".join(result.lines()))
    if result.firing:
        print(f"{PROGRAM}: a burn-rate rule is firing", file=sys.stderr)
        return EXIT_BREACH
    if result.exhausted:
        print(f"{PROGRAM}: the error budget is spent", file=sys.stderr)
        return EXIT_BREACH
    return EXIT_OK


def command_demo(args: argparse.Namespace) -> int:
    steps = demo.run()
    if args.json:
        print(json.dumps(demo.payload(steps), indent=2, sort_keys=True))
    else:
        print(demo.render(steps))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_BREACH


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    report = subparsers.add_parser("report", help="burn rate, budget and the page rules")
    _add_report_arguments(report)
    report.set_defaults(handler=command_report)
    show = subparsers.add_parser("demo", help="five reports where the arithmetic is the argument")
    show.add_argument("--json", action="store_true")
    show.set_defaults(handler=command_demo)
    check = subparsers.add_parser("selftest", help="the claims, without the prose")
    check.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (SloError, ValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
