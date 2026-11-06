"""The command line: a tree per run, and a report that shows its shape."""

from __future__ import annotations

import argparse
import sys

from .draws import DEFAULT_SEED, DrawError
from .keys import KeyValueError, describe
from .streams import StreamError, load_keys, synthetic
from .treap import Treap, TreapError
from .workload import WorkloadError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _tree(args: argparse.Namespace) -> Treap:
    pairs = load_keys(args.keys_file) if args.keys_file else synthetic(
        args.count, args.seed
    )
    tree = Treap(args.seed)
    for key, value in pairs:
        tree.insert(key, value)
    return tree


def _command_build(args: argparse.Namespace) -> int:
    tree = _tree(args)
    for line in tree.lines():
        print(line)
    stats = tree.stats()
    print(f"draws    {stats['draws']} draw(s) spent on the shape")
    return EXIT_OK


def _command_rank(args: argparse.Namespace) -> int:
    tree = _tree(args)
    print(f"tree     {len(tree)} key(s), seed {tree.seed}")
    for text in args.probes:
        key = int(text) if text.lstrip("-").isdigit() else text
        print(f"{describe(key):>12}  rank {tree.rank(key)}")
    return EXIT_OK


def _command_select(args: argparse.Namespace) -> int:
    tree = _tree(args)
    print(f"tree     {len(tree)} key(s), seed {tree.seed}")
    answer = EXIT_OK
    for position in args.positions:
        try:
            key, value = tree.select(position)
        except TreapError as error:
            print(f"position {position:>4}  holds nothing ({error})")
            answer = EXIT_NONE
        else:
            print(f"position {position:>4}  {describe(key)!r} = {value!r}")
    return answer


def _command_split(args: argparse.Namespace) -> int:
    tree = _tree(args)
    pivot = int(args.pivot) if args.pivot.lstrip("-").isdigit() else args.pivot
    under, over = tree.split(pivot)
    joined = Treap.join(under, over)
    print(f"under    {len(under)} key(s) below {describe(pivot)!r}")
    print(f"over     {len(over)} key(s) from {describe(pivot)!r} up")
    print(f"join     restores the tree: {joined.pairs() == tree.pairs()}")
    return EXIT_OK if joined.pairs() == tree.pairs() else EXIT_NONE


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
        description="A search tree that is also a heap, kept so by split and merge.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load a tree and print the shape the draws left"
    )
    build_parser_.add_argument("--keys", dest="keys_file", default=None)
    build_parser_.add_argument("--count", type=int, default=64)
    build_parser_.add_argument("--seed", type=int, default=DEFAULT_SEED)
    build_parser_.set_defaults(handler=_command_build)

    rank_parser = subparsers.add_parser(
        "rank", help="how many stored keys sit below each key given"
    )
    rank_parser.add_argument("--keys", dest="keys_file", default=None)
    rank_parser.add_argument("--count", type=int, default=64)
    rank_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    rank_parser.add_argument("probes", nargs="+")
    rank_parser.set_defaults(handler=_command_rank)

    select_parser = subparsers.add_parser(
        "select", help="the pair sitting at each position given"
    )
    select_parser.add_argument("--keys", dest="keys_file", default=None)
    select_parser.add_argument("--count", type=int, default=64)
    select_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    select_parser.add_argument("positions", nargs="+", type=int)
    select_parser.set_defaults(handler=_command_select)

    split_parser = subparsers.add_parser(
        "split", help="cut the tree at a pivot and merge the halves back"
    )
    split_parser.add_argument("--keys", dest="keys_file", default=None)
    split_parser.add_argument("--count", type=int, default=64)
    split_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    split_parser.add_argument("pivot")
    split_parser.set_defaults(handler=_command_split)

    subparsers.add_parser("demo", help="six stories about heaps and order").set_defaults(
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
    except (
        StreamError,
        TreapError,
        DrawError,
        WorkloadError,
        KeyValueError,
        OSError,
    ) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
