"""The command line: one question per run, the oracle consulted first.

search answers the index, contains answers present/absent,
lower_bound answers the first >=, audit checks a corpus, demo
tells the stories, selftest runs the promises. Every answer is
computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .solve import SearchError, audit, contains, lower_bound, search

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _values_of(tokens: list) -> list:
    out = []
    for t in tokens:
        try:
            out.append(int(t))
        except ValueError:
            raise SearchError(f"no integer label: {t!r}") from None
    return out


def _command_search(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values[:-1])
        target = int(args.values[-1])
    except (SearchError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        idx = search(values, target)
    except SearchError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(values, (target,))
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(idx))
        return EXIT_OK
    print(f"values     {len(values)}")
    print(f"target     {target}")
    print(f"index      {idx}")
    return EXIT_OK


def _command_contains(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values[:-1])
        target = int(args.values[-1])
    except (SearchError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        present = contains(values, target)
    except SearchError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(present))
        return EXIT_OK
    print(f"present    {present}")
    return EXIT_OK


def _command_lower_bound(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values[:-1])
        target = int(args.values[-1])
    except (SearchError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        lb = lower_bound(values, target)
    except SearchError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(lb))
        return EXIT_OK
    print(f"lower_bound {lb}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except SearchError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(values, tuple(values[:5]))
    if breaks:
        for b in breaks:
            print(f"{PROGRAM}: {b}", file=sys.stderr)
        return EXIT_BROKE
    print(f"audit      {len(values)} values, 0 breaks")
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
        prog=PROGRAM, description="sorted arrays, honestly searched.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="values and a target, index out")
    search_parser.add_argument("values", nargs="+")
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(handler=_command_search)

    contains_parser = subparsers.add_parser("contains", help="values and a target")
    contains_parser.add_argument("values", nargs="+")
    contains_parser.add_argument("--json", action="store_true")
    contains_parser.set_defaults(handler=_command_contains)

    lb_parser = subparsers.add_parser("lower_bound", help="values and a target, first >= out")
    lb_parser.add_argument("values", nargs="+")
    lb_parser.add_argument("--json", action="store_true")
    lb_parser.set_defaults(handler=_command_lower_bound)

    audit_parser = subparsers.add_parser("audit", help="values, audited")
    audit_parser.add_argument("values", nargs="+")
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
    except SearchError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
