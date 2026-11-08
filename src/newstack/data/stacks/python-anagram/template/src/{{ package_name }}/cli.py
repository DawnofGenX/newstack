"""The command line: one question per run, the oracle consulted first.

is_anagram answers yes/no, signature shows sorted letters, audit
checks a corpus, demo tells the stories, selftest runs the promises.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import AnagramError, audit, is_anagram, signature

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_is_anagram(args: argparse.Namespace) -> int:
    try:
        ip = is_anagram(args.a, args.b)
    except AnagramError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(ip))
        return EXIT_OK
    print(f"is_anagram  {ip}")
    return EXIT_OK


def _command_signature(args: argparse.Namespace) -> int:
    try:
        sig = signature(args.s)
    except AnagramError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(sig))
        return EXIT_OK
    print(f"signature   {sig}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    pairs = [(args.values[i], args.values[i + 1]) for i in range(0, len(args.values) - 1, 2)]
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
        prog=PROGRAM, description="small strings, honestly anagrammed.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ia = subparsers.add_parser("is_anagram", help="a b, yes/no out")
    ia.add_argument("a")
    ia.add_argument("b")
    ia.add_argument("--json", action="store_true")
    ia.set_defaults(handler=_command_is_anagram)

    sg = subparsers.add_parser("signature", help="s, sorted letters out")
    sg.add_argument("s")
    sg.add_argument("--json", action="store_true")
    sg.set_defaults(handler=_command_signature)

    a = subparsers.add_parser("audit", help="a b pairs, audited")
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
    except AnagramError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
