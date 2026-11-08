"""The command line: one question per run."""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import BracketError, count_unmatched, is_valid, matched_pairs

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _command_validate(args) -> int:
    try:
        got = is_valid(args.text)
    except BracketError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"valid      {got}")
    return EXIT_OK


def _command_pairs(args) -> int:
    try:
        got = matched_pairs(args.text)
    except BracketError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"pairs      {got}")
    return EXIT_OK


def _command_count(args) -> int:
    try:
        got = count_unmatched(args.text)
    except BracketError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"unmatched  {got}")
    return EXIT_OK


def _command_demo(_args) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def _command_selftest(_args) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="bracket matching over small strings.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="is the string valid?")
    p.add_argument("text")
    p.add_argument("--json", action="store_true")
    p.set_defaults(handler=_command_validate)

    p = sub.add_parser("pairs", help="list matched pairs")
    p.add_argument("text")
    p.add_argument("--json", action="store_true")
    p.set_defaults(handler=_command_pairs)

    p = sub.add_parser("count", help="count unmatched")
    p.add_argument("text")
    p.set_defaults(handler=_command_count)

    sub.add_parser("demo", help="stories").set_defaults(handler=_command_demo)
    sub.add_parser("selftest", help="promises").set_defaults(handler=_command_selftest)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except BracketError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
