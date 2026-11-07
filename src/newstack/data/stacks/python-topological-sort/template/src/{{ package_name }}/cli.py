"""The command line: one question per run, the picker consulted first.

order answers the listing, check answers whether a listing holds,
cycles answers the block, report counts a corpus, demo tells the
stories, selftest runs the promises. Every answer is computed
against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .cycle import cycle
from .demo import stories
from .graph import GraphError, parse_graph
from .oracle import naive_order
from .order import OrderError, block, order, validate

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _graph_of(tokens: list):
    return parse_graph(" ".join(tokens))


def _command_order(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    listed = order(graph)
    if args.json:
        print(json.dumps({"order": list(listed)}))
        return EXIT_OK
    print(">".join(str(node) for node in listed))
    if listed != naive_order(graph) or validate(graph, listed):
        print(f"{PROGRAM}: the order drifted from the picker", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_check(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    listing = [int(token) for token in args.listing.split(">")]
    breaks = validate(graph, listing)
    if breaks:
        print(f"broken: {breaks[0]}")
        return EXIT_BROKE
    print("holds: every edge points forward, every node once")
    return EXIT_OK


def _command_cycles(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    named = cycle(graph)
    if named is None:
        print("clear: nothing tangles this graph")
        return EXIT_OK
    print(f"cycle {'>'.join(str(node) for node in named)}")
    if not args.json:
        return EXIT_OK
    print(json.dumps({"cycle": list(named), "block": list(block(graph))}))
    return EXIT_OK


def _command_report(args: argparse.Namespace) -> int:
    for line in report_lines(load_graphs(args.corpus)):
        print(line)
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
        prog=PROGRAM,
        description="small digraphs, honestly ordered.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    order_parser = subparsers.add_parser(
        "order", help="a graph in, the predecessors-first listing out"
    )
    order_parser.add_argument("graph", nargs="+")
    order_parser.add_argument("--json", action="store_true")
    order_parser.set_defaults(handler=_command_order)

    check_parser = subparsers.add_parser("check", help="a listing against a graph")
    check_parser.add_argument("listing")
    check_parser.add_argument("graph", nargs="+")
    check_parser.set_defaults(handler=_command_check)

    cycles_parser = subparsers.add_parser("cycles", help="the block, named or clear")
    cycles_parser.add_argument("graph", nargs="+")
    cycles_parser.add_argument("--json", action="store_true")
    cycles_parser.set_defaults(handler=_command_cycles)

    report_parser = subparsers.add_parser("report", help="a corpus, walked")
    report_parser.add_argument("--corpus", required=True)
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
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (GraphError, CorpusError, OrderError, KeyError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
