"""The command line: one question per run, and changes counted in unit steps."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_words
from .demo import stories
from .distance import DistanceError, distance, rank_pairs
from .words import WordError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _command_distance(args: argparse.Namespace) -> int:
    left = args.left
    right = args.right
    spent = distance(left, right)
    if args.json:
        payload = {"left": left, "right": right, "distance": spent}
        print(json.dumps(payload, indent=2))
    else:
        print(f"left       {left!r}")
        print(f"right      {right!r}")
        print(f"distance   {spent}")
    return EXIT_OK


def _command_nearest(args: argparse.Namespace) -> int:
    corpus = load_words(args.words)
    query = args.query
    ranked = rank_pairs(query, corpus)
    best = ranked[0]
    rivals = [word for value, word in ranked if value == best[0]]
    if args.json:
        payload = {
            "query": query,
            "nearest": best[1],
            "distance": best[0],
            "tied": rivals,
            "ranking": [{"word": word, "distance": value} for value, word in ranked],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"query      {query!r}")
        print(f"nearest    {best[1]!r} at {best[0]}")
        print(f"tied       {len(rivals)} word(s) at {best[0]}: {', '.join(rivals)}")
    return EXIT_OK if best[0] == 0 else EXIT_MISS


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
        description="Unit-cost edit distance over lowercase strings: "
        "distance, nearest, selftest, demo.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    distance_parser = subparsers.add_parser(
        "distance", help="the fewest unit changes between two strings"
    )
    distance_parser.add_argument("left", metavar="LEFT")
    distance_parser.add_argument("right", metavar="RIGHT")
    distance_parser.add_argument("--json", action="store_true")
    distance_parser.set_defaults(handler=_command_distance)

    nearest_parser = subparsers.add_parser(
        "nearest", help="the corpus entry with the smallest distance"
    )
    nearest_parser.add_argument("--words", required=True, help="one word per line")
    nearest_parser.add_argument("query", metavar="QUERY")
    nearest_parser.add_argument("--json", action="store_true")
    nearest_parser.set_defaults(handler=_command_nearest)

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
    except (CorpusError, DistanceError, WordError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
