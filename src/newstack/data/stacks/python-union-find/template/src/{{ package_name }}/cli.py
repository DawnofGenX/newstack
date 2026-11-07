"""The command line: one question per run, and a report that names the roots.

Every question takes a workload file (``a b`` per line) or a pair of
elements, and answers from a forest rebuilt fresh on each run — except
``selftest``, which interrogates the modules directly.
"""

from __future__ import annotations

import argparse
import json
import sys

from .forest import (
    Shape,
    UnionFind,
    UnionFindError,
)
from .pairs import (
    PairError,
    load_pairs,
    synthetic,
)

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _forest(args: argparse.Namespace) -> UnionFind:
    forest = UnionFind()
    for first, second in load_pairs(args.pairs):
        forest.add(first)
        forest.add(second)
    for first, second in load_pairs(args.pairs):
        forest.union(first, second)
    return forest


def _payload(forest: UnionFind, shape: Shape, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "elements": shape.elements,
        "components": shape.components,
        "max_depth": shape.max_depth,
        "roots_rewritten": shape.roots_rewritten,
    }
    payload.update(extra)
    return payload


def _command_build(args: argparse.Namespace) -> int:
    forest = _forest(args)
    if args.json:
        print(json.dumps(_payload(forest, forest.shape(), {}), indent=2))
        return EXIT_OK
    shape = forest.shape()
    print(f"elements   {shape.elements}, components {shape.components}")
    print(f"depth      {shape.max_depth}")
    for group in forest.components():
        print("  " + " ".join(str(member) for member in group))
    return EXIT_OK


def _command_add(args: argparse.Namespace) -> int:
    forest = _forest(args)
    opened = forest.add(args.element)
    if args.json:
        print(
            json.dumps(
                _payload(forest, forest.shape(), {"element": args.element, "opened": opened}),
                indent=2,
            )
        )
    else:
        print(f"element    {args.element}")
        print(f"opened     {opened}")
    return EXIT_OK if opened else EXIT_NONE


def _command_union(args: argparse.Namespace) -> int:
    forest = _forest(args)
    merged = forest.union(args.first, args.second)
    if args.json:
        print(
            json.dumps(
                _payload(
                    forest,
                    forest.shape(),
                    {"pair": [args.first, args.second], "merged": merged},
                ),
                indent=2,
            )
        )
    else:
        print(f"pair       {args.first} {args.second}")
        print(f"merged     {merged}")
    return EXIT_OK if merged else EXIT_NONE


def _command_connected(args: argparse.Namespace) -> int:
    forest = _forest(args)
    joined = forest.connected(args.first, args.second)
    if args.json:
        print(
            json.dumps(
                _payload(
                    forest,
                    forest.shape(),
                    {"pair": [args.first, args.second], "joined": joined},
                ),
                indent=2,
            )
        )
    else:
        print(f"pair       {args.first} {args.second}")
        print(f"joined     {joined}")
    return EXIT_OK if joined else EXIT_NONE


def _command_components(args: argparse.Namespace) -> int:
    forest = _forest(args)
    groups = forest.components()
    if args.json:
        print(json.dumps(_payload(forest, forest.shape(), {"groups": groups}), indent=2))
    else:
        print(f"components {len(groups)}")
        for group in groups:
            print("  " + " ".join(str(member) for member in group))
    return EXIT_OK if groups else EXIT_NONE


def _command_count(args: argparse.Namespace) -> int:
    forest = _forest(args)
    shape = forest.shape()
    if args.json:
        print(json.dumps(_payload(forest, shape, {}), indent=2))
    else:
        print(f"elements   {shape.elements}")
        print(f"components {shape.components}")
    return EXIT_OK if shape.components else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A disjoint-set forest: union by size, find with compression.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build", help="join a workload, list the partition")
    _workload_args(build_parser_)
    build_parser_.add_argument("--json", action="store_true")
    build_parser_.set_defaults(handler=_command_build)

    add_parser = subparsers.add_parser("add", help="open one element's component")
    _workload_args(add_parser)
    add_parser.add_argument("--element", type=int, required=True)
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    union_parser = subparsers.add_parser("union", help="merge two components")
    _workload_args(union_parser)
    _pair_args(union_parser)
    union_parser.add_argument("--json", action="store_true")
    union_parser.set_defaults(handler=_command_union)

    joined_parser = subparsers.add_parser("connected", help="do two walks share a name")
    _workload_args(joined_parser)
    _pair_args(joined_parser)
    joined_parser.add_argument("--json", action="store_true")
    joined_parser.set_defaults(handler=_command_connected)

    groups_parser = subparsers.add_parser("components", help="enumerate every component")
    _workload_args(groups_parser)
    groups_parser.add_argument("--json", action="store_true")
    groups_parser.set_defaults(handler=_command_components)

    count_parser = subparsers.add_parser("count", help="count the components of a workload")
    _workload_args(count_parser)
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    demo_parser = subparsers.add_parser("demo", help="a fixed forest, stated plainly")
    demo_parser.add_argument("--json", action="store_true")
    demo_parser.set_defaults(handler=_command_demo)

    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def _command_demo(args: argparse.Namespace) -> int:
    forest = UnionFind(range(9))
    for first, second in synthetic(6, seed=7, low=0, high=9):
        forest.union(first, second)
    shape = forest.shape()
    if args.json:
        print(json.dumps(_payload(forest, shape, {"groups": forest.components()}), indent=2))
        return EXIT_OK
    print("a forest of nine, joined by a seeded six")
    for group in forest.components():
        print("  " + " ".join(str(member) for member in group))
    print(f"depth      {shape.max_depth} before any ask")
    return EXIT_OK


def _workload_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pairs", required=True, help="one 'a b' pair per line")


def _pair_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--second", type=int, required=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (UnionFindError, PairError, UsageError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
