"""The command line: a tree per run, and a report that shows its cells."""

from __future__ import annotations

import argparse
import sys

from .fenwick import Fenwick, FenwickError
from .streams import StreamError, load_values, synthetic
from .values import ValueRejection

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _tree(args: argparse.Namespace) -> Fenwick:
    values = load_values(args.values_file) if args.values_file else synthetic(
        args.count, args.seed
    )
    return Fenwick(values)


def _whole(text: str) -> int:
    try:
        return int(text)
    except ValueError as error:
        raise UsageError(f"{text!r} is no whole number ({error})") from error


def _command_build(args: argparse.Namespace) -> int:
    tree = _tree(args)
    for line in tree.lines():
        print(line)
    stats = tree.stats()
    print(
        f"walk-limit {stats['limit']} longest {stats['longest']}"
        f" total {stats['total']} invariant {stats['invariant']}"
    )
    return EXIT_OK


def _command_add(args: argparse.Namespace) -> int:
    tree = _tree(args)
    print(f"tree     {len(tree)} values, walk-limit {tree.limit}")
    try:
        walk = tree.add(_whole(args.index), _whole(args.delta))
    except (FenwickError, ValueRejection, UsageError) as error:
        print(f"{args.index!r} is no seat ({error})")
        return EXIT_UNUSABLE
    print(f"added    {walk.line()}")
    return EXIT_OK if tree.invariant() else EXIT_NONE


def _command_sum(args: argparse.Namespace) -> int:
    tree = _tree(args)
    try:
        walk = tree.prefix(_whole(args.count))
    except (FenwickError, ValueRejection, UsageError) as error:
        print(f"{args.count!r} is no count ({error})")
        return EXIT_UNUSABLE
    print(f"prefix   {walk.line()}")
    return EXIT_OK


def _command_range(args: argparse.Namespace) -> int:
    tree = _tree(args)
    try:
        low, high = _whole(args.low), _whole(args.high)
        walk = tree.range_sum(low, high)
    except (FenwickError, ValueRejection, UsageError) as error:
        print(f"the window [{args.low}..{args.high}) is unusable ({error})")
        return EXIT_UNUSABLE
    print(f"range    {walk.line()}")
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
        description="Integer values in, prefix sums out, in a bit-length of steps.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load a tree and print the cells as they stand"
    )
    build_parser_.add_argument("--values", dest="values_file", default=None)
    build_parser_.add_argument("--count", type=int, default=64)
    build_parser_.add_argument("--seed", type=int, default=7)
    build_parser_.set_defaults(handler=_command_build)

    add_parser = subparsers.add_parser(
        "add", help="shift values and show the climb the cells took"
    )
    add_parser.add_argument("--values", dest="values_file", default=None)
    add_parser.add_argument("--count", type=int, default=64)
    add_parser.add_argument("--seed", type=int, default=7)
    add_parser.add_argument("index")
    add_parser.add_argument("delta")
    add_parser.set_defaults(handler=_command_add)

    sum_parser = subparsers.add_parser(
        "sum", help="the prefix of this many values, walked down the bits"
    )
    sum_parser.add_argument("--values", dest="values_file", default=None)
    sum_parser.add_argument("--count", type=int, default=64)
    sum_parser.add_argument("--seed", type=int, default=7)
    sum_parser.add_argument("count")
    sum_parser.set_defaults(handler=_command_sum)

    range_parser = subparsers.add_parser(
        "range", help="the window between two indices, two prefixes deep"
    )
    range_parser.add_argument("--values", dest="values_file", default=None)
    range_parser.add_argument("--count", type=int, default=64)
    range_parser.add_argument("--seed", type=int, default=7)
    range_parser.add_argument("low")
    range_parser.add_argument("high")
    range_parser.set_defaults(handler=_command_range)

    subparsers.add_parser("demo", help="six stories about cells and bits").set_defaults(
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
    except (StreamError, FenwickError, ValueRejection, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
