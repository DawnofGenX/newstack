"""The command line: one question per run, the oracle consulted first.

distances answers the map, cycles answers the honest negative-cycle
name, report counts a corpus, demo tells the stories, selftest runs
the promises. Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .cycle import negative_cycle
from .demo import stories
from .graph import UNREACHED, Graph, GraphError, parse_graph
from .oracle import oracle_distances
from .walk import audit, distances, settled

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _render(answer: dict) -> str:
    rows = {node: cost for node, cost in sorted(answer.items())}
    return json.dumps(rows)


def _graph_of(tokens: list) -> Graph:
    return parse_graph(" ".join(tokens))


def _command_distances(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    answer = distances(graph, args.source)
    breaks = audit(graph, args.source, answer)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(_render(answer))
        return EXIT_OK
    print(f"nodes      {len(graph)}")
    print(f"source     {args.source}")
    for node, cost in sorted(answer.items()):
        shown = "unreached" if cost is UNREACHED else cost
        print(f"  distance   {node} {shown}")
    if answer != oracle_distances(graph, args.source):
        print(f"{PROGRAM}: the walker drifted from the oracle", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_cycles(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    cycle = negative_cycle(graph, args.source)
    if args.json:
        payload = {
            "source": args.source,
            "cycle": list(cycle) if cycle else None,
            "settled": not settled(graph, args.source),
        }
        print(json.dumps(payload))
    else:
        print(f"source     {args.source}")
        print(f"cycle      {list(cycle) if cycle else 'none'}")
        print(f"settled    {not settled(graph, args.source)}")
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
        description="small weighted digraphs, honestly walked.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    distances_parser = subparsers.add_parser(
        "distances", help="a weighted graph in, its distance map out"
    )
    distances_parser.add_argument("graph", nargs="+")
    distances_parser.add_argument("--source", type=int, required=True)
    distances_parser.add_argument("--json", action="store_true")
    distances_parser.set_defaults(handler=_command_distances)

    cycles_parser = subparsers.add_parser(
        "cycles", help="a weighted graph in, its negative cycle named"
    )
    cycles_parser.add_argument("graph", nargs="+")
    cycles_parser.add_argument("--source", type=int, required=True)
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
    except (GraphError, CorpusError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
