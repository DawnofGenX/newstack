"""The command line: a map per run, and a report that shows its shape."""

from __future__ import annotations

import argparse
import sys

from .coins import DEFAULT_SEED, CoinTossError
from .keys import SkipKeyValueError, describe
from .map import SkipList, SkipListError
from .stack import CorpusError, load_pairs, synthetic

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _key(text: str) -> object:
    """Read a key off the command line: an int, a float, or the text."""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def _map(args: argparse.Namespace) -> SkipList:
    pairs = load_pairs(args.pairs) if args.pairs else synthetic(args.count, args.seed)
    filled = SkipList(seed=args.seed)
    for key, value in pairs:
        filled.insert(key, value)
    return filled


def _command_build(args: argparse.Namespace) -> int:
    filled = _map(args)
    for line in filled.lines():
        print(line)
    stats = filled.stats()
    print(f"flips    {stats['flips']} coin flip(s) spent on the shape")
    return EXIT_OK


def _command_rank(args: argparse.Namespace) -> int:
    filled = _map(args)
    print(f"map      {len(filled)} key(s), seed {filled.seed}")
    for text in args.keys:
        key = _key(text)
        print(f"{describe(key):>12}  rank {filled.rank(key)}")
    return EXIT_OK


def _command_select(args: argparse.Namespace) -> int:
    filled = _map(args)
    print(f"map      {len(filled)} key(s), seed {filled.seed}")
    answer = EXIT_OK
    for position in args.positions:
        try:
            key, value = filled.select(position)
        except SkipListError as error:
            print(f"position {position:>4}  holds nothing ({error})")
            answer = EXIT_NONE
        else:
            print(f"position {position:>4}  {describe(key)!r} = {value!r}")
    return answer


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
        description="A sorted map that balances on coin flips, not rotations.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load a map and print the shape the coins left"
    )
    build_parser_.add_argument("--pairs", default=None)
    build_parser_.add_argument("--count", type=int, default=64)
    build_parser_.add_argument("--seed", type=int, default=DEFAULT_SEED)
    build_parser_.set_defaults(handler=_command_build)

    rank_parser = subparsers.add_parser(
        "rank", help="how many stored keys sit below each key given"
    )
    rank_parser.add_argument("--pairs", default=None)
    rank_parser.add_argument("--count", type=int, default=64)
    rank_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    rank_parser.add_argument("keys", nargs="+")
    rank_parser.set_defaults(handler=_command_rank)

    select_parser = subparsers.add_parser(
        "select", help="the pair sitting at each position given"
    )
    select_parser.add_argument("--pairs", default=None)
    select_parser.add_argument("--count", type=int, default=64)
    select_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    select_parser.add_argument("positions", nargs="+", type=int)
    select_parser.set_defaults(handler=_command_select)

    subparsers.add_parser("demo", help="six stories about coins and order").set_defaults(
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
    except (CorpusError, SkipListError, CoinTossError, SkipKeyValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
