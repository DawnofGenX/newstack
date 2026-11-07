"""The command line: one question per run, the array in order."""

from __future__ import annotations

import argparse
import json
import sys

from .array import ArrayError, ZArray, occurrences
from .corpus import CorpusError
from .demo import stories
from .word import WordError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _preview(values: list[int], limit: int = 24) -> str:
    shown = values[:limit]
    tail = "" if len(values) <= limit else f", ... ({len(values)} total)"
    return f"{shown}{tail}"


def _command_zarray(args: argparse.Namespace) -> int:
    cut = ZArray(args.word)
    if args.json:
        payload = {"word": args.word, "array": list(cut.array)}
        print(json.dumps(payload, indent=2))
    else:
        print(f"word       {args.word!r}")
        print(f"length     {len(cut.array)}")
        print(f"array      {_preview(list(cut.array))}")
    return EXIT_OK


def _command_occurrences(args: argparse.Namespace) -> int:
    starts = occurrences(args.word, args.pattern)
    if args.json:
        payload = {
            "word": args.word,
            "pattern": args.pattern,
            "starts": starts,
            "first": starts[0] if starts else None,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"word       {args.word!r}")
        print(f"starts     {_preview(starts)}")
        print(f"first      {starts[0] if starts else None}")
    return EXIT_OK if starts else EXIT_MISS


def _command_count(args: argparse.Namespace) -> int:
    hits = len(occurrences(args.word, args.pattern))
    if args.json:
        payload = {"word": args.word, "pattern": args.pattern, "count": hits}
        print(json.dumps(payload, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"count      {hits}")
    return EXIT_OK if hits else EXIT_MISS


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
        description="The Z-array over lowercase words: zarray, occurrences, count.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    zarray_parser = subparsers.add_parser("zarray", help="the array of a word")
    zarray_parser.add_argument("--word", required=True)
    zarray_parser.add_argument("--json", action="store_true")
    zarray_parser.set_defaults(handler=_command_zarray)

    find_parser = subparsers.add_parser(
        "occurrences", help="every start, the concatenated array's answer"
    )
    find_parser.add_argument("--pattern", required=True)
    find_parser.add_argument("word")
    find_parser.add_argument("--json", action="store_true")
    find_parser.set_defaults(handler=_command_occurrences)

    count_parser = subparsers.add_parser("count", help="how many starts are owed")
    count_parser.add_argument("--pattern", required=True)
    count_parser.add_argument("word")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

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
    except (ArrayError, CorpusError, WordError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
