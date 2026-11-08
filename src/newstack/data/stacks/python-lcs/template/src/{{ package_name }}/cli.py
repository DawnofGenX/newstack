"""The command line: one question per run, the oracle consulted first."""

from __future__ import annotations

import argparse
import json
import sys

from .solve import LcsError, audit, lcs, lcs_length

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_lcs(args: argparse.Namespace) -> int:
    try:
        c = lcs(args.a, args.b)
    except LcsError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"lcs           {c!r}")
    return EXIT_OK


def _command_len(args: argparse.Namespace) -> int:
    try:
        c = lcs_length(args.a, args.b)
    except LcsError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"lcs_length    {c}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    pairs = [(v.split(",")[0], v.split(",", 1)[1]) for v in args.values]
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
    from .demo import stories

    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description="small strings, honestly matched.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lc = subparsers.add_parser("lcs", help="a b, lcs out")
    lc.add_argument("a")
    lc.add_argument("b")
    lc.add_argument("--json", action="store_true")
    lc.set_defaults(handler=_command_lcs)

    ln = subparsers.add_parser("len", help="a b, length out")
    ln.add_argument("a")
    ln.add_argument("b")
    ln.add_argument("--json", action="store_true")
    ln.set_defaults(handler=_command_len)

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
    except LcsError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
