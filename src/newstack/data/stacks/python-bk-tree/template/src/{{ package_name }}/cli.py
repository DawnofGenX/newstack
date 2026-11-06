"""The command line: one query per run, and a report that names what it looked at."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_words
from .distance import DistanceError, measurement
from .tree import BKTree, Search, TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _words(args: argparse.Namespace) -> list[str]:
    return load_words(args.words, lowercase=args.lowercase)


def _payload(found: Search) -> dict[str, object]:
    return {
        "query": found.query,
        "max_distance": found.max_distance,
        "corpus": found.corpus,
        "visited": found.visited,
        "compared": found.compared,
        "full_scan": found.full_scan,
        "hits": [{"word": hit.word, "distance": hit.distance} for hit in found.hits],
    }


def _command_distance(args: argparse.Namespace) -> int:
    plain = measurement(args.left, args.right, limit=args.limit)
    swapped = measurement(args.left, args.right, limit=args.limit, transpositions=True)
    limit = "" if args.limit is None else f", limit {args.limit}"
    print(f"left       {args.left!r}")
    print(f"right      {args.right!r}")
    print(f"edits      {plain.distance}   ({plain.cells} cell(s), {plain.rows} row(s){limit})")
    print(
        f"with osa   {swapped.distance}   "
        f"({swapped.cells} cell(s), {swapped.rows} row(s){limit})"
    )
    return EXIT_OK


def _command_search(args: argparse.Namespace) -> int:
    tree = BKTree(_words(args))
    if args.transpositions:
        found = tree.search_allowing_transpositions(args.word, args.distance)
    else:
        found = tree.search(args.word, args.distance)
    if args.json:
        print(json.dumps(_payload(found), indent=2))
        return EXIT_OK if found.hits else EXIT_NONE
    for line in found.lines():
        print(line)
    if not found.hits:
        print("verdict    nothing within that distance")
        return EXIT_NONE
    return EXIT_OK


def _command_nearest(args: argparse.Namespace) -> int:
    tree = BKTree(_words(args))
    found = tree.nearest(args.word)
    if args.json:
        print(json.dumps(_payload(found), indent=2))
        return EXIT_OK
    print(f"query      {found.query!r}")
    print(f"corpus     {found.corpus} word(s)")
    print(f"looked at  {found.visited} node(s), {found.compared} distance(s) computed")
    print(f"closest    {found.max_distance}")
    for hit in found.hits:
        print(hit.line())
    return EXIT_OK


def _command_tree(args: argparse.Namespace) -> int:
    words = _words(args)
    tree = BKTree(words)
    print(f"corpus     {len(words)} line(s), {len(tree)} distinct word(s)")
    print(f"depth      {tree.depth}")
    print(f"root       {tree.words[0]!r}")
    query = args.word if args.word else tree.words[0]
    radius = args.distance
    pruned = tree.search(query, radius)
    scanned = tree.scan(query, radius)
    print(f"query      {query!r} within {radius}")
    print(f"tree       {pruned.visited} node(s) visited")
    print(f"scan       {scanned.visited} word(s) compared")
    print(f"same set   {pruned.words == scanned.words}")
    return EXIT_OK


def _command_demo(_args: argparse.Namespace) -> int:
    from .demo import render_stories

    print(render_stories())
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Find words by how far they are from a query, without comparing every word.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    distance_parser = subparsers.add_parser(
        "distance", help="the edit distance between two strings"
    )
    distance_parser.add_argument("left")
    distance_parser.add_argument("right")
    distance_parser.add_argument("--limit", type=int, default=None)
    distance_parser.set_defaults(handler=_command_distance)

    search_parser = subparsers.add_parser("search", help="every word within a distance")
    search_parser.add_argument("--words", required=True)
    search_parser.add_argument("--word", required=True)
    search_parser.add_argument("--distance", type=int, default=1)
    search_parser.add_argument("--transpositions", action="store_true")
    search_parser.add_argument("--lowercase", action="store_true")
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(handler=_command_search)

    nearest_parser = subparsers.add_parser("nearest", help="the closest words, however far")
    nearest_parser.add_argument("--words", required=True)
    nearest_parser.add_argument("--word", required=True)
    nearest_parser.add_argument("--lowercase", action="store_true")
    nearest_parser.add_argument("--json", action="store_true")
    nearest_parser.set_defaults(handler=_command_nearest)

    tree_parser = subparsers.add_parser(
        "tree", help="the shape of the tree, and one walk through it"
    )
    tree_parser.add_argument("--words", required=True)
    tree_parser.add_argument("--word", default=None)
    tree_parser.add_argument("--distance", type=int, default=1)
    tree_parser.add_argument("--lowercase", action="store_true")
    tree_parser.set_defaults(handler=_command_tree)

    subparsers.add_parser("demo", help="six stories about searching by distance").set_defaults(
        handler=_command_demo
    )
    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (CorpusError, DistanceError, TreeError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
