"""The command line: one question per run, starts in table order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_texts
from .demo import stories
from .suffix import SuffixError, build
from .text import TextError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _table(args: argparse.Namespace):  # type: ignore[no-untyped-def]
    return build(load_texts(args.texts)[0])


def _payload(table, extra: dict[str, object]) -> dict[str, object]:  # type: ignore[no-untyped-def]
    payload: dict[str, object] = {
        "text": table.text,
        "suffixes": len(table),
        "array": table.array,
    }
    payload.update(extra)
    return payload


def _preview(table, limit: int = 20) -> str:  # type: ignore[no-untyped-def]
    shown = table.array[:limit]
    tail = "" if len(table.array) <= limit else f", ... ({len(table.array)} total)"
    return f"{shown}{tail}"


def _command_build(args: argparse.Namespace) -> int:
    table = _table(args)
    if args.json:
        print(json.dumps(_payload(table, {}), indent=2))
    else:
        print(f"text       {table.text!r}")
        print(f"suffixes   {len(table)}")
        print(f"array      {_preview(table)}")
    return EXIT_OK


def _command_count(args: argparse.Namespace) -> int:
    table = _table(args)
    found = table.count(args.pattern)
    if args.json:
        payload = _payload(table, {"pattern": args.pattern, "count": found,
                                   "positions": table.positions(args.pattern)})
        print(json.dumps(payload, indent=2))
    else:
        print(f"pattern    {args.pattern!r}")
        print(f"count      {found}")
        for start in table.positions(args.pattern):
            print(f"  at {start:<4} {table.suffix_at(start)!r}")
    return EXIT_OK if found else EXIT_MISS


def _command_lrs(args: argparse.Namespace) -> int:
    table = _table(args)
    repeat = table.longest_repeat()
    if args.json:
        payload = _payload(table, {"repeat": repeat, "height": len(repeat)})
        print(json.dumps(payload, indent=2))
    else:
        print(f"repeat     {repeat!r}")
        print(f"height     {len(repeat)}")
    return EXIT_OK if repeat else EXIT_MISS


def _command_lcp(args: argparse.Namespace) -> int:
    table = _table(args)
    shared = table.lcp(args.left, args.right)
    if args.json:
        payload = _payload(table, {"left": args.left, "right": args.right,
                                   "shares": shared})
        print(json.dumps(payload, indent=2))
    else:
        print(f"suffixes   {args.left} and {args.right}")
        print(f"shares     {shared}")
    return EXIT_OK if shared else EXIT_MISS


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


def _text_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--texts", required=True, help="one text per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Sorted suffix starts of a text: build, count, lrs, lcp.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build", help="the sorted starts")
    _text_args(build_parser_)
    build_parser_.add_argument("--json", action="store_true")
    build_parser_.set_defaults(handler=_command_build)

    count_parser = subparsers.add_parser("count", help="starts holding a pattern")
    _text_args(count_parser)
    count_parser.add_argument("pattern", metavar="PATTERN")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    lrs_parser = subparsers.add_parser("lrs", help="the longest repeated text")
    _text_args(lrs_parser)
    lrs_parser.add_argument("--json", action="store_true")
    lrs_parser.set_defaults(handler=_command_lrs)

    lcp_parser = subparsers.add_parser("lcp", help="share of two suffixes")
    _text_args(lcp_parser)
    lcp_parser.add_argument("left", type=int, metavar="I")
    lcp_parser.add_argument("right", type=int, metavar="J")
    lcp_parser.add_argument("--json", action="store_true")
    lcp_parser.set_defaults(handler=_command_lcp)

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
    except (CorpusError, TextError, SuffixError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
