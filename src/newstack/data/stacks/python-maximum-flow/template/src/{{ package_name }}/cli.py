"""The command line: one question per run, the enumeration consulted first.

flow answers the value, map answers the shipped arcs, report counts
a corpus, demo tells the stories, selftest runs the promises.
Every answer is computed against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_graphs, report_lines
from .demo import stories
from .graph import GraphError, parse_graph
from .oracle import min_cut
from .solve import FlowError, audit, flow_map, max_flow

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _render(shipped: dict) -> str:
    return json.dumps(
        [{"arc": list(arc), "shipped": amount}
         for arc, amount in sorted(shipped.items())]
    )


def _network_of(tokens: list):
    return parse_graph(" ".join(tokens))


def _command_flow(args: argparse.Namespace) -> int:
    graph = _network_of(args.graph)
    walked = max_flow(graph, args.source, args.sink)
    if args.json:
        print(json.dumps({"source": args.source, "sink": args.sink, "flow": walked}))
        return EXIT_OK
    print(f"source     {args.source}")
    print(f"sink       {args.sink}")
    print(f"flow       {walked}")
    if walked != min_cut(graph, args.source, args.sink):
        print(f"{PROGRAM}: the walker drifted from the enumeration", file=sys.stderr)
        return EXIT_BROKE
    return EXIT_OK


def _command_map(args: argparse.Namespace) -> int:
    graph = _network_of(args.graph)
    shipped = flow_map(graph, args.source, args.sink)
    breaks = audit(graph, args.source, args.sink, shipped)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(_render(shipped))
        return EXIT_OK
    print(f"source     {args.source}")
    print(f"sink       {args.sink}")
    print(f"flow       {max_flow(graph, args.source, args.sink)}")
    for arc, amount in sorted(shipped.items()):
        print(f"  {arc[0]}->{arc[1]} ships {amount}")
    if max_flow(graph, args.source, args.sink) != min_cut(graph, args.source, args.sink):
        print(f"{PROGRAM}: the map drifts from the enumeration", file=sys.stderr)
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
        description="small digraphs, honestly carried.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    flow_parser = subparsers.add_parser(
        "flow", help="a network and its ends in, the carried value out"
    )
    flow_parser.add_argument("source", type=int)
    flow_parser.add_argument("sink", type=int)
    flow_parser.add_argument("graph", nargs="+")
    flow_parser.add_argument("--json", action="store_true")
    flow_parser.set_defaults(handler=_command_flow)

    map_parser = subparsers.add_parser(
        "map", help="a network and its ends in, the shipped arcs out"
    )
    map_parser.add_argument("source", type=int)
    map_parser.add_argument("sink", type=int)
    map_parser.add_argument("graph", nargs="+")
    map_parser.add_argument("--json", action="store_true")
    map_parser.set_defaults(handler=_command_map)

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
    except (GraphError, CorpusError, FlowError, KeyError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
