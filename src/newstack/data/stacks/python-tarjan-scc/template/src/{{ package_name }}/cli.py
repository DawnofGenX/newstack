"""The command line: one question per run, the oracle consulted first.

components answers the partition, condense answers the DAG, report
counts a corpus, demo tells the stories, selftest runs the
promises. Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .cycle import has_cycle
from .demo import stories
from .graph import GraphError, parse_graph
from .oracle import oracle_partition
from .scc import audit, condense, partition

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _render(groups: tuple) -> str:
    rows = [sorted(group) for group in groups]
    return json.dumps(rows)


def _components_of(tokens: list) -> tuple:
    graph = parse_graph(" ".join(tokens))
    return graph, partition(graph)


def _command_components(args: argparse.Namespace) -> int:
    graph, groups = _components_of(args.graph)
    breaks = audit(graph, groups)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(_render(groups))
        return EXIT_OK
    print(f"nodes      {len(graph)}")
    print(f"components {len(groups)}")
    for group in groups:
        print(f"  component {sorted(group)}")
    if groups != oracle_partition(graph):
        print(f"{PROGRAM}: the walker drifted from the oracle", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_condense(args: argparse.Namespace) -> int:
    graph = parse_graph(" ".join(args.graph))
    dag = condense(graph)
    cycle = has_cycle(dag)
    if args.json:
        payload = {
            "heads": sorted(dag.nodes()),
            "edges": [list(edge) for edge in dag.edges()],
            "acyclic": cycle is None,
        }
        print(json.dumps(payload))
    else:
        print(f"heads      {sorted(dag.nodes())}")
        print(f"edges      {list(dag.edges())}")
        print(f"acyclic    {cycle is None}")
    return EXIT_OK if cycle is None else EXIT_BROKE


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
        description="small digraphs, honestly partitioned.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    components_parser = subparsers.add_parser(
        "components", help="a graph in, its components out"
    )
    components_parser.add_argument("graph", nargs="+")
    components_parser.add_argument("--json", action="store_true")
    components_parser.set_defaults(handler=_command_components)

    condense_parser = subparsers.add_parser(
        "condense", help="a graph in, the DAG of components out"
    )
    condense_parser.add_argument("graph", nargs="+")
    condense_parser.add_argument("--json", action="store_true")
    condense_parser.set_defaults(handler=_command_condense)

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
