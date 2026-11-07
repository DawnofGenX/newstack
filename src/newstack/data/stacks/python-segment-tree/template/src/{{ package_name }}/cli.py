"""The command line: a ladder per run, and answers that show their visits."""

from __future__ import annotations

import argparse
import sys

from .array import ArrayValueError, load_values, synthetic
from .tree import SegmentError, SegmentTree, addition, minimum

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_OUTSIDE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _tree(args: argparse.Namespace) -> SegmentTree:
    values = (
        load_values(args.values_file)
        if args.values_file
        else synthetic(args.count, args.seed)
    )
    fold = minimum if args.mode == "min" else addition
    return SegmentTree(values, fold)


def _command_build(args: argparse.Namespace) -> int:
    tree = _tree(args)
    shown = list(tree.leaves())
    print(f"array  {shown[:12]}{' ...' if tree.n > 12 else ''}")
    print(f"fold   {args.mode} root {tree.root} invariant {tree.invariant()}")
    print(f"shape  size {tree.size} bound {2 * tree.n.bit_length()} nodes")
    return EXIT_OK


def _command_query(args: argparse.Namespace) -> int:
    tree = _tree(args)
    try:
        answer = tree.query(args.low, args.high)
    except SegmentError as error:
        print(f"window {error}")
        return EXIT_OUTSIDE
    print(
        f"query  [{args.low}, {args.high}) = {answer}"
        f" visits {tree.visits} bound {2 * tree.n.bit_length()}"
    )
    return EXIT_OK


def _command_set(args: argparse.Namespace) -> int:
    tree = _tree(args)
    try:
        tree.set(args.index, args.value)
    except SegmentError as error:
        print(f"index {error}")
        return EXIT_OUTSIDE
    print(
        f"set    {args.index} -> {args.value} root {tree.root}"
        f" invariant {tree.invariant()}"
    )
    return EXIT_OK


def _command_add(args: argparse.Namespace) -> int:
    tree = _tree(args)
    try:
        landed = tree.add(args.index, args.delta)
    except SegmentError as error:
        print(f"index {error}")
        return EXIT_OUTSIDE
    print(
        f"add    {args.index} by {args.delta} -> {landed}"
        f" root {tree.root} invariant {tree.invariant()}"
    )
    return EXIT_OK


def _command_demo(_args: argparse.Namespace) -> int:
    from .demo import render_stories

    print(render_stories())
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_OUTSIDE


def _fold_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--values", dest="values_file", default=None)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--mode", choices=("sum", "min"), default="sum")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A segment tree over an integer array, seam and all.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load an array and print the ladder over it"
    )
    _fold_option(build_parser_)
    build_parser_.set_defaults(handler=_command_build)

    query_parser = subparsers.add_parser(
        "query", help="answer [LOW, HIGH) and count the nodes visited"
    )
    _fold_option(query_parser)
    query_parser.add_argument("low", type=int)
    query_parser.add_argument("high", type=int)
    query_parser.set_defaults(handler=_command_query)

    set_parser = subparsers.add_parser("set", help="drop a value on an index")
    _fold_option(set_parser)
    set_parser.add_argument("index", type=int)
    set_parser.add_argument("value", type=int)
    set_parser.set_defaults(handler=_command_set)

    add_parser = subparsers.add_parser("add", help="slide an index by a delta")
    _fold_option(add_parser)
    add_parser.add_argument("index", type=int)
    add_parser.add_argument("delta", type=int)
    add_parser.set_defaults(handler=_command_add)

    subparsers.add_parser(
        "demo", help="six stories about ladders and windows"
    ).set_defaults(handler=_command_demo)
    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        handler = args.handler
        return int(handler(args))
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (ArrayValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
