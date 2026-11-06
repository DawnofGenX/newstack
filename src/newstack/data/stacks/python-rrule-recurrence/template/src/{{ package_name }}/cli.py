"""Command line for the recurrence expander."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import demo as demo_module
from .expand import Expansion, expand
from .explain import Decision, explain
from .rrule import Rule, RuleError, parse

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line asked for something that cannot be answered."""


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise UsageError(f"{name!r} is not a time zone name this machine knows") from error


def _wall(text: str, label: str) -> datetime:
    try:
        moment = datetime.fromisoformat(text)
    except ValueError as error:
        raise UsageError(f"{label}={text!r} is not an ISO time like 2026-03-08T02:30") from error
    if moment.tzinfo is not None:
        raise UsageError(
            f"{label}={text!r} carries an offset; a recurrence is a wall time, so pass it without "
            "one and name the zone with --zone"
        )
    return moment


def _rule(text: str) -> Rule:
    if len(text.strip()) <= 8:
        raise UsageError(f"--rule={text!r} is too short to be a rule, e.g. FREQ=DAILY;COUNT=3")
    return parse(text)


def _expansion_payload(expansion: Expansion) -> dict[str, object]:
    return {
        "rule": expansion.rule.text,
        "start": expansion.start.isoformat(),
        "zone": str(expansion.zone),
        "occurrences": [
            {
                "index": item.index,
                "local": item.local.isoformat(),
                "instant": item.instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            for item in expansion.occurrences
        ],
        "skipped": [
            {"local": item.local.isoformat(), "reason": item.reason} for item in expansion.skipped
        ],
        "stopped": expansion.stopped,
    }


def _command_next(args: argparse.Namespace) -> int:
    rule = _rule(args.rule)
    start = _wall(args.start, "--start")
    zone = _zone(args.zone)
    expansion = expand(rule, start, zone, limit=args.count, span_years=args.span_years)
    if args.json:
        print(json.dumps(_expansion_payload(expansion), indent=2, sort_keys=True))
    else:
        print(f"rule       {rule.text}")
        print(f"start      {start.strftime('%Y-%m-%d %H:%M:%S')} {args.zone}")
        for line in rule.lines():
            print(line)
        print("  idx  local                 utc")
        for item in expansion.occurrences:
            print(item.line())
        for item in expansion.skipped:
            print(item.line())
        print(f"stopped    {expansion.stopped}")
    return EXIT_OK if expansion.occurrences else EXIT_NO_MATCH


def _command_between(args: argparse.Namespace) -> int:
    rule = _rule(args.rule)
    start = _wall(args.start, "--start")
    lower = _wall(args.since, "--since")
    upper = _wall(args.until, "--until")
    if upper < lower:
        raise UsageError("--until is before --since, so the window is empty by construction")
    zone = _zone(args.zone)
    expansion = expand(rule, start, zone, span_years=args.span_years)
    kept = [item for item in expansion.occurrences if lower <= item.local <= upper]
    expansion.occurrences = kept
    if args.json:
        print(json.dumps(_expansion_payload(expansion), indent=2, sort_keys=True))
    else:
        print(f"rule       {rule.text}")
        print(f"window     {lower.isoformat()} .. {upper.isoformat()} {args.zone}")
        for item in kept:
            print(item.line())
        print(f"firings    {len(kept)}")
    return EXIT_OK if kept else EXIT_NO_MATCH


def _decision_payload(decision: Decision) -> dict[str, object]:
    return {
        "at": decision.at.isoformat(),
        "occurrence": decision.occurrence,
        "reasons": decision.reasons,
    }


def _command_explain(args: argparse.Namespace) -> int:
    rule = _rule(args.rule)
    start = _wall(args.start, "--start")
    at = _wall(args.at, "--at")
    zone = _zone(args.zone)
    decision = explain(rule, start, zone, at)
    if args.json:
        print(json.dumps(_decision_payload(decision), indent=2, sort_keys=True))
    else:
        print(f"rule       {rule.text}")
        print(f"start      {start.isoformat()} {args.zone}")
        for line in decision.lines():
            print(line)
    return EXIT_OK if decision.occurrence else EXIT_NO_MATCH


def _command_demo(args: argparse.Namespace) -> int:
    del args
    return demo_module.run()


def _command_selftest(args: argparse.Namespace) -> int:
    del args
    from . import selftest

    return selftest.run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="expand a recurrence rule into instants, and say why each one is there",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    nxt = sub.add_parser("next", help="the next firings of a rule")
    nxt.add_argument("--rule", required=True, help="RRULE text, e.g. FREQ=WEEKLY;BYDAY=MO;COUNT=4")
    nxt.add_argument(
        "--start", required=True, help="wall time of the first candidate, e.g. 2026-01-05T09:00"
    )
    nxt.add_argument("--zone", default="UTC", help="IANA zone the wall times belong to")
    nxt.add_argument("--count", type=int, default=8, help="how many firings to print")
    nxt.add_argument(
        "--span-years",
        type=int,
        default=40,
        help="how many years to scan before concluding a rule never fires",
    )
    nxt.add_argument("--json", action="store_true", help="print the expansion as JSON")
    nxt.set_defaults(handler=_command_next)

    between = sub.add_parser("between", help="firings inside a window")
    between.add_argument("--rule", required=True, help="RRULE text")
    between.add_argument("--start", required=True, help="wall time of the first candidate")
    between.add_argument("--since", required=True, help="window start, inclusive")
    between.add_argument("--until", required=True, help="window end, inclusive")
    between.add_argument("--zone", default="UTC", help="IANA zone the wall times belong to")
    between.add_argument("--span-years", type=int, default=4, help="how far to scan for firings")
    between.add_argument("--json", action="store_true", help="print the window as JSON")
    between.set_defaults(handler=_command_between)

    asked = sub.add_parser("explain", help="why a wall time is or is not a firing")
    asked.add_argument("--rule", required=True, help="RRULE text")
    asked.add_argument("--start", required=True, help="wall time of the first candidate")
    asked.add_argument("--at", required=True, help="the wall time to judge")
    asked.add_argument("--zone", default="UTC", help="IANA zone the wall times belong to")
    asked.add_argument("--json", action="store_true", help="print the decision as JSON")
    asked.set_defaults(handler=_command_explain)

    demo = sub.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = sub.add_parser("selftest", help="check the rule engine against known answers")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (UsageError, RuleError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
