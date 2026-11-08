"""The command line: one question per run, the generator consulted first.

comb answers every ordering, count answers the factorial, unique
answers distinct orderings, audit names any shape that fails, demo
tells the stories, selftest runs the promises. Every answer is
computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import CombinationError, audit, combinations, count, unique

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _items_of(tokens: list) -> list:
    return list(tokens)


def _command_comb(args: argparse.Namespace) -> int:
    try:
        items = _items_of(args.items)
        got = combinations(items)
    except CombinationError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(items)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"items      {len(items)}")
    print(f"count      {len(got)}")
    print(f"combs      {got}")
    return EXIT_OK


def _command_count(args: argparse.Namespace) -> int:
    try:
        n = int(args.n)
    except ValueError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        c = count(n)
    except CombinationError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c))
        return EXIT_OK
    print(f"count      {c}")
    return EXIT_OK


def _command_unique(args: argparse.Namespace) -> int:
    try:
        items = _items_of(args.items)
        got = unique(items)
    except CombinationError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"unique     {len(got)}")
    print(f"combs      {got}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    try:
        items = _items_of(args.items)
        breaks = audit(items)
    except CombinationError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if breaks:
        for b in breaks:
            print(f"break      {b}")
        return EXIT_BROKE
    print("audit      clean")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def _command_demo(_args: argparse.Namespace) -> int:
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
        prog=PROGRAM, description="small lists, honestly combuted.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    comb_parser = subparsers.add_parser("comb", help="items in, every ordering out")
    comb_parser.add_argument("items", nargs="+")
    comb_parser.add_argument("--json", action="store_true")
    comb_parser.set_defaults(handler=_command_comb)

    count_parser = subparsers.add_parser("count", help="n in, factorial out")
    count_parser.add_argument("n")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    unique_parser = subparsers.add_parser("unique", help="items in, distinct orderings out")
    unique_parser.add_argument("items", nargs="+")
    unique_parser.add_argument("--json", action="store_true")
    unique_parser.set_defaults(handler=_command_unique)

    audit_parser = subparsers.add_parser("audit", help="items in, shape check out")
    audit_parser.add_argument("items", nargs="+")
    audit_parser.set_defaults(handler=_command_audit)

    selftest_parser = subparsers.add_parser("selftest", help="the promises")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except CombinationError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
