"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, demo, plan
from .audit import causality_breaks, coverage
from .stamp import StampError, parse_stamp
from .world import DEFAULT_START_MS, WorldError

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_UNUSABLE = 2


class UsageError(Exception):
    """The command line asked for something that cannot be answered."""


def command_demo(args) -> int:
    sys.stdout.write(demo.render())
    return EXIT_OK if all(story.held for story in demo.stories()) else EXIT_BROKEN


def command_plan(args) -> int:
    events = plan.load(Path(args.plan))
    world = plan.execute(events, start_ms=args.start, max_skew_ms=args.max_skew)
    breaks = causality_breaks(world.messages)
    if args.json:
        print(json.dumps(world.as_dict(), indent=2, sort_keys=True))
    else:
        print("stamps")
        for line in world.stamp_lines():
            print(f"  {line}")
        print("report")
        for line in world.reports():
            print(f"  {line}")
        print("coverage")
        for node, seen in coverage(world).items():
            print(
                f"  {node:<8} events {seen['events']:<4} receipts {seen['receives']:<4}"
                f" wall jumps {seen['forward_jumps']:<3} skew {seen['skew_ms']} ms"
            )
        print(f"messages     {len(world.messages)}")
        print(f"causal breaks {len(breaks)}")
        for line in breaks:
            print(f"  {line}")
    if breaks:
        return EXIT_BROKEN
    if args.max_skew is not None:
        worst = world.max_skew()
        if worst > args.max_skew:
            if not args.json:
                print(f"skew         {worst} ms is past the {args.max_skew} ms bound")
            return EXIT_BROKEN
    return EXIT_OK


def command_stamp(args) -> int:
    stamp = parse_stamp(args.text)
    print(f"stamp        {stamp.text()}")
    print(f"key          {stamp.key()}")
    return EXIT_OK


def command_selftest(args) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="hybrid logical clocks you can audit"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("plan", help="run a plan of events from a file")
    run.add_argument("--plan", required=True)
    run.add_argument("--start", type=int, default=DEFAULT_START_MS)
    run.add_argument("--max-skew", type=int)
    run.add_argument("--json", action="store_true")
    run.set_defaults(handler=command_plan)

    stamp = subparsers.add_parser("stamp", help="read a stamp back into its parts")
    stamp.add_argument("text")
    stamp.set_defaults(handler=command_stamp)

    demo_parser = subparsers.add_parser("demo", help="run the six stories")
    demo_parser.set_defaults(handler=command_demo)

    selftest_parser = subparsers.add_parser("selftest", help="run the built-in checks")
    selftest_parser.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (UsageError, StampError, WorldError, plan.PlanError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
