"""The command line: one question per run, the oracle consulted first.

convert answers the binary string, read answers the decimal value,
audit checks pairs, demo tells the stories, selftest runs the promises.
Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import ConversionError, audit, binary_to_decimal, dec_to_binary

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_convert(args: argparse.Namespace) -> int:
    try:
        value = int(args.value)
    except ValueError:
        print(f"{PROGRAM}: no integer label: {args.value!r}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = dec_to_binary(value)
    except ConversionError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"decimal    {value}")
    print(f"binary     {got}")
    return EXIT_OK


def _command_read(args: argparse.Namespace) -> int:
    text = args.value
    try:
        got = binary_to_decimal(text)
    except ConversionError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"binary     {text}")
    print(f"decimal    {got}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    pairs = []
    for token in args.pairs:
        if "," not in token:
            print(f"{PROGRAM}: bad pair: {token!r}", file=sys.stderr)
            return EXIT_UNUSABLE
        left, right = token.split(",", 1)
        try:
            pairs.append((int(left.strip()), right.strip()))
        except ValueError:
            print(f"{PROGRAM}: bad pair: {token!r}", file=sys.stderr)
            return EXIT_UNUSABLE
    breaks = audit(pairs)
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps([]))
        return EXIT_OK
    print(f"pairs      {len(pairs)}")
    print("audit      clean")
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
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="decimal to binary conversion, honestly done."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    c = subparsers.add_parser("convert", help="decimal in, binary out")
    c.add_argument("value")
    c.add_argument("--json", action="store_true")
    c.set_defaults(handler=_command_convert)

    r = subparsers.add_parser("read", help="binary in, decimal out")
    r.add_argument("value")
    r.add_argument("--json", action="store_true")
    r.set_defaults(handler=_command_read)

    a = subparsers.add_parser("audit", help="pairs in, breaks out")
    a.add_argument("pairs", nargs="+")
    a.add_argument("--json", action="store_true")
    a.set_defaults(handler=_command_audit)

    st = subparsers.add_parser("selftest", help="the promises")
    st.set_defaults(handler=_command_selftest)

    d = subparsers.add_parser("demo", help="stories, computed live")
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
    except ConversionError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())