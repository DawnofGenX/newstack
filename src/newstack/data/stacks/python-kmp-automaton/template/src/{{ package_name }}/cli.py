"""The command line: one question per run, starts in order."""

from __future__ import annotations

import argparse
import json
import sys

from .automaton import AutomatonError, KmpAutomaton, failure_table
from .corpus import CorpusError
from .demo import stories
from .pattern import PatternError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _preview(starts: list[int], limit: int = 20) -> str:
    shown = starts[:limit]
    tail = "" if len(starts) <= limit else f", ... ({len(starts)} total)"
    return f"{shown}{tail}"


def _command_find(args: argparse.Namespace) -> int:
    automaton = KmpAutomaton(args.pattern)
    starts = automaton.find_all(args.text)
    if args.json:
        payload = {
            "pattern": args.pattern,
            "text": args.text,
            "starts": starts,
            "first": automaton.find_first(args.text),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"starts     {_preview(starts)}")
        print(f"first      {automaton.find_first(args.text)}")
    return EXIT_OK if starts else EXIT_MISS


def _command_count(args: argparse.Namespace) -> int:
    automaton = KmpAutomaton(args.pattern)
    hits = automaton.count(args.text)
    if args.json:
        payload = {"pattern": args.pattern, "text": args.text, "count": hits}
        print(json.dumps(payload, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"count      {hits}")
    return EXIT_OK if hits else EXIT_MISS


def _command_table(args: argparse.Namespace) -> int:
    table = failure_table(args.pattern)
    if args.json:
        print(json.dumps({"pattern": args.pattern, "table": list(table)}, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"states     {len(table)}")
        for state, link in enumerate(table):
            print(f"  {state}      {link}")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_MISS


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_MISS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Knuth-Morris-Pratt over lowercase text: find, count, table.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser("find", help="every start, overlaps kept")
    find_parser.add_argument("--pattern", required=True)
    find_parser.add_argument("text")
    find_parser.add_argument("--json", action="store_true")
    find_parser.set_defaults(handler=_command_find)

    count_parser = subparsers.add_parser("count", help="how many starts are owed")
    count_parser.add_argument("--pattern", required=True)
    count_parser.add_argument("text")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    table_parser = subparsers.add_parser("table", help="the failure table")
    table_parser.add_argument("--pattern", required=True)
    table_parser.add_argument("--json", action="store_true")
    table_parser.set_defaults(handler=_command_table)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (AutomatonError, CorpusError, PatternError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
