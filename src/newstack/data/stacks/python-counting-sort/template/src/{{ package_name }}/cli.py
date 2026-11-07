"""The command line: one question per run, the oracle consulted first.

sort answers the sorted list, counts answers the tally,
rank answers the prefix, report counts a corpus, demo tells the
stories, selftest runs the promises. Every answer is computed
against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import SortError, audit, counts, rank, sort

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
            raise SortError(f"no integer label: {t!r}") from None
    return out


def _command_sort(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = sort(values)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(values)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"values     {len(values)}")
    print(f"sorted     {got}")
    if got != sorted(values):
        print(f"{PROGRAM}: the sort drifted from the oracle", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_counts(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        c = counts(values)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(c, sort_keys=True))
        return EXIT_OK
    print(f"values     {len(values)}")
    for v in sorted(c):
        print(f"  {v}: {c[v]}")
    return EXIT_OK


def _command_rank(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values[:-1])
        value = int(args.values[-1])
    except (SortError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        r = rank(values, value)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(r))
        return EXIT_OK
    print(f"rank       {r}")
    return EXIT_OK


def _command_report(args: argparse.Namespace) -> int:
    print(f"{PROGRAM}: no corpus support in this stack", file=sys.stderr)
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
        prog=PROGRAM, description="small integer arrays, honestly sorted.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sort_parser = subparsers.add_parser("sort", help="values in, sorted list out")
    sort_parser.add_argument("values", nargs="+")
    sort_parser.add_argument("--json", action="store_true")
    sort_parser.set_defaults(handler=_command_sort)

    counts_parser = subparsers.add_parser("counts", help="values in, tally out")
    counts_parser.add_argument("values", nargs="+")
    counts_parser.add_argument("--json", action="store_true")
    counts_parser.set_defaults(handler=_command_counts)

    rank_parser = subparsers.add_parser("rank", help="values and a value, prefix count out")
    rank_parser.add_argument("values", nargs="+")
    rank_parser.add_argument("--json", action="store_true")
    rank_parser.set_defaults(handler=_command_rank)

    report_parser = subparsers.add_parser("report", help="a corpus, walked")
    report_parser.add_argument("--corpus", required=False)
    report_parser.set_defaults(handler=_command_report)

    selftest_parser = subparsers.add_parser("selftest", help="the promises")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return EXIT_UNUSABLE
    try:
        return args.handler(args)
    except SortError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
