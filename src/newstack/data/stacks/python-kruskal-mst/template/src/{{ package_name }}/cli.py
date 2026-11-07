"""The command line: one question per run, the oracle consulted first.

tree answers the edge set, witness answers the walk's ledger,
report counts a corpus, demo tells the stories, selftest runs the
promises. Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .demo import stories
from .graph import GraphError, parse_graph
from .oracle import min_cost
from .solve import TreeError, audit, spanning_tree, tree_cost, witness

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _render(edges: frozenset) -> str:
    return json.dumps(
        [{"edge": list(edge_pair), "weight": weight}
         for edge_pair, weight in sorted(edges)]
    )


def _ledger(graph) -> str:
    return json.dumps([step.to_record() for step in witness(graph)])


def _graph_of(tokens: list):
    return parse_graph(" ".join(tokens))


def _command_tree(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    edges = spanning_tree(graph)
    breaks = audit(graph, edges)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(_render(edges))
        return EXIT_OK
    print(f"nodes      {len(graph)}")
    print(f"edges      {len(edges)}")
    for edge_pair, weight in sorted(edges):
        print(f"  {edge_pair[0]}-{edge_pair[1]} at {weight}")
    if sum(weight for _pair, weight in edges) != min_cost(graph):
        print(f"{PROGRAM}: the walker drifted from the enumeration", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_witness(args: argparse.Namespace) -> int:
    graph = _graph_of(args.graph)
    steps = witness(graph)
    if args.json:
        print(_ledger(graph))
        return EXIT_OK
    print(f"edges      {len(steps)} considered")
    for step in steps:
        mark = "take" if step.taken else "skip"
        print(f"  {mark:<6} {step.edge[0]}-{step.edge[1]} at {step.weight}: {step.reason}")
    if sum(step.weight for step in steps if step.taken) != tree_cost(graph):
        print(f"{PROGRAM}: the ledger drifts from the tree", file=sys.stderr)
        return EXIT_BROKE
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
        description="small undirected graphs, honestly spanned.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tree_parser = subparsers.add_parser(
        "tree", help="a graph in, the tree's edge set out"
    )
    tree_parser.add_argument("graph", nargs="+")
    tree_parser.add_argument("--json", action="store_true")
    tree_parser.set_defaults(handler=_command_tree)

    witness_parser = subparsers.add_parser(
        "witness", help="a graph in, the walk's ledger out"
    )
    witness_parser.add_argument("graph", nargs="+")
    witness_parser.add_argument("--json", action="store_true")
    witness_parser.set_defaults(handler=_command_witness)

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
    except (GraphError, CorpusError, KeyError, TreeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
