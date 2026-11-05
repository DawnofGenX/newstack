"""Command line for a cron schedule: say the runs, in UTC and in a wall clock."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime

from . import demo, model

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_NOTHING = 1
EXIT_UNUSABLE = 2
DEFAULT_ZONE = "UTC"
DEFAULT_COUNT = 3


def _parse_moment(text: str) -> datetime:
    try:
        moment = datetime.fromisoformat(text)
    except ValueError as error:
        raise model.CronError(f"--after {text!r} is not an ISO 8601 moment: {error}") from error
    if moment.tzinfo is None:
        raise model.CronError(
            f"--after {text!r} has no offset; a moment without a zone is the bug this "
            "tool exists to make visible, so write a Z on the end"
        )
    return moment.astimezone(UTC)


def _rule_text(schedule: model.Schedule) -> str:
    if schedule.day_rule == "or":
        return "or   both fields are restricted, so either one matches (Vixie cron)"
    return "and  day-of-month is * so it cannot veto the weekday"


def command_next(args: argparse.Namespace) -> int:
    schedule = model.parse(args.expression)
    after = _parse_moment(args.after) if args.after else datetime.now(UTC)
    runs = model.runs_after(schedule, after, args.tz, count=args.count)
    if args.json:
        print(
            json.dumps(
                {
                    "expression": schedule.expression,
                    "zone": args.tz,
                    "after": after.isoformat(),
                    "runs": [run.as_dict() for run in runs],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"after    {after:%Y-%m-%dT%H:%M:%SZ}")
        print(f"zone     {args.tz}")
        for index, run in enumerate(runs, start=1):
            print(f"{index:>2}  {run.line()}")
    if not runs:
        print(
            f"{PROGRAM}: no run within {model.DEFAULT_HORIZON_YEARS} years; "
            "the expression is valid but describes nothing in that window",
            file=sys.stderr,
        )
        return EXIT_NOTHING
    return EXIT_OK


def command_explain(args: argparse.Namespace) -> int:
    schedule = model.parse(args.expression)
    fields = (
        ("minute", schedule.minute),
        ("hour", schedule.hour),
        ("day", schedule.day),
        ("month", schedule.month),
        ("weekday", schedule.weekday),
    )
    print(f"expression {schedule.expression}")
    for name, field in fields:
        values = field.text()
        meaning = "every" if field.star else values
        print(f"{name:<10} {meaning}")
    print(f"day rule   {_rule_text(schedule)}")
    return EXIT_OK


def command_demo(args: argparse.Namespace) -> int:
    steps = demo.run()
    if args.json:
        print(json.dumps(demo.payload(steps), indent=2, sort_keys=True))
    else:
        print(demo.render(steps))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_NOTHING


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    nxt = subparsers.add_parser("next", help="print the next runs of an expression")
    nxt.add_argument("expression", help='five fields, e.g. "30 2 * * *"')
    nxt.add_argument("--count", type=int, default=DEFAULT_COUNT)
    nxt.add_argument("--after", help="an ISO 8601 moment with an offset; default: now")
    nxt.add_argument("--tz", default=DEFAULT_ZONE, help="the wall clock the fields refer to")
    nxt.add_argument("--json", action="store_true")
    nxt.set_defaults(handler=command_next)

    why = subparsers.add_parser("explain", help="say what each field means")
    why.add_argument("expression")
    why.set_defaults(handler=command_explain)

    show = subparsers.add_parser("demo", help="six schedules, computed")
    show.add_argument("--json", action="store_true")
    show.set_defaults(handler=command_demo)

    self_check = subparsers.add_parser("selftest", help="the claims, without the prose")
    self_check.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except model.CronError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
