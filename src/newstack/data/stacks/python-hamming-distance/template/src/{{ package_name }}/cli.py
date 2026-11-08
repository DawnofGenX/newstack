"""The command line: one question per run, the oracle consulted first.

bits answers the bit distance, chars answers the char distance,
audit checks triples, demo tells the stories, selftest runs the promises.
Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import HammingError, audit, hamming, hamming_text

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_bits(args: argparse.Namespace) -> int:
    try:
        a = int(args.a)
        b = int(args.b)
    except ValueError:
        print(f"{PROGRAM}: no integer label", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = hamming(a, b)
    except HammingError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"hamming    {got}")
    return EXIT_OK


def _command_chars(args: argparse.Namespace) -> int:
    try:
        got = hamming_text(args.a, args.b)
    except HammingError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"hamming    {got}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    triples = []
    for token in args.triples:
        parts = token.split(",")
        if len(parts) != 3:
            print(f"{PROGRAM}: bad triple: {token!r}", file=sys.stderr)
            return EXIT_UNUSABLE
        try:
            triples.append((int(parts[0].strip()), int(parts[1].strip()), int(parts[2].strip())))
        except ValueError:
            print(f"{PROGRAM}: bad triple: {token!r}", file=sys.stderr)
            return EXIT_UNUSABLE
    breaks = audit(triples)
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps([]))
        return EXIT_OK
    print(f"triples    {len(triples)}")
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
        prog=PROGRAM, description="hamming distance, honestly done."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    b = subparsers.add_parser("bits", help="two ints in, bit distance out")
    b.add_argument("a")
    b.add_argument("b")
    b.add_argument("--json", action="store_true")
    b.set_defaults(handler=_command_bits)

    c = subparsers.add_parser("chars", help="two strings in, char distance out")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--json", action="store_true")
    c.set_defaults(handler=_command_chars)

    a = subparsers.add_parser("audit", help="triples in, breaks out")
    a.add_argument("triples", nargs="+")
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
    except HammingError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
