"""The command line: one question per run, the oracle consulted first.

fibonacci answers the n-th term, list answers the first n terms,
audit checks a corpus, demo tells the stories, selftest runs the
promises.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import FibonacciError, audit, fibonacci, fibonacci_list

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_fibonacci(args: argparse.Namespace) -> int:
    try:
        n = int(args.n)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        f = fibonacci(n)
    except FibonacciError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(f))
        return EXIT_OK
    print(f"fibonacci  {f}")
    return EXIT_OK


def _command_list(args: argparse.Namespace) -> int:
    try:
        n = int(args.n)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        ls = fibonacci_list(n)
    except FibonacciError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(ls))
        return EXIT_OK
    print(f"list       {ls}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    try:
        ns = [int(x) for x in args.values]
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(ns)
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    print(f"audit      {len(ns)} values, 0 breaks")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def _command_demo(_args: argparse.Namespace) -> int:
    told = demo_stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def demo_stories():
    from .demo import stories

    return stories()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="small n, honestly fibonaccied.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    f = subparsers.add_parser("fibonacci", help="n, fib(n) out")
    f.add_argument("n")
    f.add_argument("--json", action="store_true")
    f.set_defaults(handler=_command_fibonacci)

    lp = subparsers.add_parser("list", help="n, first n terms out")
    lp.add_argument("n")
    lp.add_argument("--json", action="store_true")
    lp.set_defaults(handler=_command_list)

    a = subparsers.add_parser("audit", help="values, audited")
    a.add_argument("values", nargs="+")
    a.set_defaults(handler=_command_audit)

    s = subparsers.add_parser("selftest", help="the promises")
    s.set_defaults(handler=_command_selftest)

    d = subparsers.add_parser("demo", help="six stories, computed live")
    d.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except FibonacciError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
