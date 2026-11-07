"""The command line: one question per run, the walker consulted first.

table answers the distance table, worst answers the most distant
pair, report counts a corpus, demo tells the stories, selftest runs
the promises. Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .demo import stories
from .graph import GraphError, parse_graph
from .oracle import OracleError, distance_table
from .solve import TableError, audit, distances, worst_hop

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _render(table: dict) -> str:
    return json.dumps(
        [{"pair": list(hop_pair), "cost": cost} for hop_pair, cost in sorted(table.items())]
    )


def _graph_of(tokens: list):
    return parse_graph(" ".join(tokens))


def _command_table(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    table = distances(graph)
    breaks = audit(graph, table)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(_render(table))
        return EXIT_OK
    print(f"pairs      {len(table)}")
    for (source, target), cost in sorted(table.items()):
        print(f"  {source}->{target} at {cost}")
    if table != distance_table(graph):
        print(f"{PROGRAM}: the table drifted from the walk", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_worst(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    source, target, cost = worst_hop(graph)
    if args.json:
        print(json.dumps({"source": source, "target": target, "cost": cost}))
        return EXIT_OK
    print(f"worst      {source}->{target}")
    print(f"cost       {cost}")
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
        description="small digraphs, honestly walked.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    table_parser = subparsers.add_parser(
        "table", help="a graph in, the all-pairs distance table out"
    )
    table_parser.add_argument("graph", nargs="+")
    table_parser.add_argument("--json", action="store_true")
    table_parser.set_defaults(handler=_command_table)

    worst_parser = subparsers.add_parser("worst", help="a graph in, the farthest pair out")
    worst_parser.add_argument("graph", nargs="+")
    worst_parser.add_argument("--json", action="store_true")
    worst_parser.set_defaults(handler=_command_worst)

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
    except (GraphError, CorpusError, KeyError, TableError, OracleError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
