"""The command line: a tree per run, and a ledger that shows its costs."""

from __future__ import annotations

import argparse
import sys

from .keys import KeyValueError, describe
from .rules import DEFAULT_ALPHA, RuleError, checked_alpha
from .streams import StreamError, load_keys, synthetic
from .tree import ScapegoatTree, TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _tree(args: argparse.Namespace) -> ScapegoatTree:
    pairs = load_keys(args.keys_file) if args.keys_file else synthetic(args.count)
    tree = ScapegoatTree(checked_alpha(args.alpha))
    for key, value in pairs:
        tree.insert(key, value)
    return tree


def _number(text: str) -> int:
    try:
        return int(text)
    except ValueError as error:
        raise UsageError(f"{text!r} is not an integer") from error


def _command_build(args: argparse.Namespace) -> int:
    tree = _tree(args)
    stats = tree.stats()
    print(
        f"size {stats['size']} depth {stats['depth']} alpha {tree.alpha}"
        f" work {stats['work']} balanced {stats['balanced']}"
    )
    return EXIT_OK


def _command_rank(args: argparse.Namespace) -> int:
    tree = _tree(args)
    print(f"tree     {len(tree)} key(s), alpha {tree.alpha}")
    for text in args.probes:
        key = _number(text)
        print(f"{describe(key):>12}  rank {tree.rank(key)}")
    return EXIT_OK


def _command_select(args: argparse.Namespace) -> int:
    tree = _tree(args)
    print(f"tree     {len(tree)} key(s), alpha {tree.alpha}")
    answer = EXIT_OK
    for position in args.positions:
        try:
            key, value = tree.select(position)
        except TreeError as error:
            print(f"position {position:>4}  holds nothing ({error})")
            answer = EXIT_NONE
        else:
            print(f"position {position:>4}  {describe(key)!r} = {value!r}")
    return answer


def _command_storm(args: argparse.Namespace) -> int:
    from .demo import _storm

    story = _storm()
    for line in story.lines:
        print(line)
    return EXIT_OK if story.held else EXIT_NONE


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
        description="A BST that rebuilds tipped subtrees and counts the bill.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load a tree and print the ledger the rebuilds left"
    )
    build_parser_.add_argument("--keys", dest="keys_file", default=None)
    build_parser_.add_argument("--count", type=int, default=64)
    build_parser_.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    build_parser_.set_defaults(handler=_command_build)

    rank_parser = subparsers.add_parser(
        "rank", help="how many stored keys sit below each key given"
    )
    rank_parser.add_argument("--keys", dest="keys_file", default=None)
    rank_parser.add_argument("--count", type=int, default=64)
    rank_parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    rank_parser.add_argument("probes", nargs="+")
    rank_parser.set_defaults(handler=_command_rank)

    select_parser = subparsers.add_parser(
        "select", help="the pair sitting at each position given"
    )
    select_parser.add_argument("--keys", dest="keys_file", default=None)
    select_parser.add_argument("--count", type=int, default=64)
    select_parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    select_parser.add_argument("positions", nargs="+", type=int)
    select_parser.set_defaults(handler=_command_select)

    storm_parser = subparsers.add_parser(
        "storm", help="run the seeded mixed storm and report the rule"
    )
    storm_parser.set_defaults(handler=_command_storm)

    subparsers.add_parser("demo", help="six stories, every claim computed").set_defaults(
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
        TreeError,
        RuleError,
        KeyValueError,
        OSError,
    ) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
