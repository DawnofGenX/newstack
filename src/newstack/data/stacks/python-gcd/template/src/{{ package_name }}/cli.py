"""The command line: one question per run, the oracle consulted first."""

from __future__ import annotations

import argparse
import json
import sys

from .solve import GcdError, audit, extended_gcd, gcd, mod_inverse

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_gcd(args: argparse.Namespace) -> int:
    try:
        c = gcd(args.a, args.b)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"gcd           {c}")
    return EXIT_OK


def _command_ext(args: argparse.Namespace) -> int:
    try:
        g, x, y = extended_gcd(args.a, args.b)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps({"g": g, "x": x, "y": y}))
        return EXIT_OK
    print(f"extended_gcd  g={g} x={x} y={y}")
    return EXIT_OK


def _command_inv(args: argparse.Namespace) -> int:
    try:
        c = mod_inverse(args.a, args.m)
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"mod_inverse   {c}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    pairs = [(int(x), int(y)) for x, y in (v.split(",") for v in args.values)]
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
        prog=PROGRAM, description="small integers, honestly divided.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    g = subparsers.add_parser("gcd", help="a b, gcd out")
    g.add_argument("a", type=int)
    g.add_argument("b", type=int)
    g.add_argument("--json", action="store_true")
    g.set_defaults(handler=_command_gcd)

    e = subparsers.add_parser("ext", help="a b, extended gcd out")
    e.add_argument("a", type=int)
    e.add_argument("b", type=int)
    e.add_argument("--json", action="store_true")
    e.set_defaults(handler=_command_ext)

    inv = subparsers.add_parser("inv", help="a m, inverse out")
    inv.add_argument("a", type=int)
    inv.add_argument("m", type=int)
    inv.add_argument("--json", action="store_true")
    inv.set_defaults(handler=_command_inv)

    a = subparsers.add_parser("audit", help="pairs, audited")
    a.add_argument("values", nargs="+")
    a.set_defaults(handler=_command_audit)

    st = subparsers.add_parser("selftest", help="the promises")
    st.set_defaults(handler=_command_selftest)

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
    except GcdError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
