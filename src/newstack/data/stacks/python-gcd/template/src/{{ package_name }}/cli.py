"""The command line: one question per run, the oracle consulted first.

gcd answers the greatest common divisor, lcm the least common
multiple, coprime reports shared divisors, audit checks a corpus,
demo tells the stories, selftest runs the promises.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import GcdError, audit, coprime, gcd, lcm

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_gcd(args: argparse.Namespace) -> int:
    try:
        a = int(args.a)
        b = int(args.b)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        g = gcd(a, b)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(g))
        return EXIT_OK
    print(f"gcd        {g}")
    return EXIT_OK


def _command_lcm(args: argparse.Namespace) -> int:
    try:
        a = int(args.a)
        b = int(args.b)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        result = lcm(a, b)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(result))
        return EXIT_OK
    print(f"lcm        {result}")
    return EXIT_OK


def _command_coprime(args: argparse.Namespace) -> int:
    try:
        a = int(args.a)
        b = int(args.b)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        c = coprime(a, b)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"coprime    {c}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    try:
        xs = args.values[::2]
        ys = args.values[1::2]
        pairs = [(int(x), int(y)) for x, y in zip(xs, ys, strict=False)]
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(pairs)
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    print(f"audit      {len(pairs)} pairs, 0 breaks")
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
        prog=PROGRAM, description="small positive integers, honestly divided.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gcd_p = subparsers.add_parser("gcd", help="a and b, gcd out")
    gcd_p.add_argument("a")
    gcd_p.add_argument("b")
    gcd_p.add_argument("--json", action="store_true")
    gcd_p.set_defaults(handler=_command_gcd)

    lcm_p = subparsers.add_parser("lcm", help="a and b, lcm out")
    lcm_p.add_argument("a")
    lcm_p.add_argument("b")
    lcm_p.add_argument("--json", action="store_true")
    lcm_p.set_defaults(handler=_command_lcm)

    cp_p = subparsers.add_parser("coprime", help="a and b, coprime out")
    cp_p.add_argument("a")
    cp_p.add_argument("b")
    cp_p.add_argument("--json", action="store_true")
    cp_p.set_defaults(handler=_command_coprime)

    audit_p = subparsers.add_parser("audit", help="pairs, audited")
    audit_p.add_argument("values", nargs="+")
    audit_p.set_defaults(handler=_command_audit)

    selftest_p = subparsers.add_parser("selftest", help="the promises")
    selftest_p.set_defaults(handler=_command_selftest)

    demo_p = subparsers.add_parser("demo", help="six stories, computed live")
    demo_p.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
