"""Command line entry point: `demo`, `selftest`, and nothing else.

The library is the product; the CLI is the harness that makes its behaviour readable in a
terminal, which is what a code review actually needs.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import demo
from . import selftest as selftest_mod

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_UNUSABLE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A circuit breaker whose state machine is the product.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="print a scripted outage as a timeline")
    demo_parser.add_argument("--failures", type=int, default=3, help="failures before the trip")
    demo_parser.add_argument("--cooldown", type=float, default=30.0, help="cooldown seconds")
    demo_parser.add_argument("--successes", type=int, default=2, help="healthy calls first")
    demo_parser.add_argument("--json", action="store_true", help="print the timeline as JSON")

    subparsers.add_parser("selftest", help="run the built-in checks")
    return parser


def payload(timeline: demo.Timeline) -> dict[str, object]:
    return {
        "ok": timeline.ok,
        "steps": [
            {
                "at": step.at,
                "label": step.label,
                "state": str(step.state),
                "allowed": step.decision.allowed,
                "reason": step.decision.reason,
                "retry_in": step.decision.retry_in,
            }
            for step in timeline.steps
        ],
    }


def command_demo(args: argparse.Namespace) -> int:
    timeline = demo.run(failures=args.failures, cooldown=args.cooldown, successes=args.successes)
    if args.json:
        print(json.dumps(payload(timeline), indent=2))
    else:
        for line in timeline.lines():
            print(line)
        print()
        for line in timeline.summary():
            print(line)
    return EXIT_OK if timeline.ok else EXIT_MISMATCH


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            return command_demo(args)
        if args.command == "selftest":
            return selftest_mod.run()
    except (ValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    return EXIT_UNUSABLE
