"""The command line: one question per run, the oracle consulted first.

factorial answers n!, binomial answers C(n,k), audit checks a
corpus, demo tells the stories, selftest runs the promises.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import FactorialError, audit, binomial, factorial

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_factorial(args: argparse.Namespace) -> int:
    try:
        n = int(args.n)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        f = factorial(n)
    except FactorialError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(f))
        return EXIT_OK
    print(f"factorial  {f}")
    return EXIT_OK


def _command_binomial(args: argparse.Namespace) -> int:
    try:
        n = int(args.n)
        k = int(args.k)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        b = binomial(n, k)
    except FactorialError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(b))
        return EXIT_OK
    print(f"binomial   {b}")
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
        prog=PROGRAM, description="small n, honestly factorialled.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    f = subparsers.add_parser("factorial", help="n, n! out")
    f.add_argument("n")
    f.add_argument("--json", action="store_true")
    f.set_defaults(handler=_command_factorial)

    b = subparsers.add_parser("binomial", help="n k, C(n,k) out")
    b.add_argument("n")
    b.add_argument("k")
    b.add_argument("--json", action="store_true")
    b.set_defaults(handler=_command_binomial)

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
    except FactorialError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
