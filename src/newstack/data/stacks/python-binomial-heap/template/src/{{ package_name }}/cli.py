"""The command line: a forest per run, and a report that shows its ranks."""

from __future__ import annotations

import argparse
import sys

from .heap import BinomialHeap, HeapError
from .keys import KeyValueError, bits, describe
from .streams import StreamError, load_keys, synthetic

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _heap(args: argparse.Namespace) -> BinomialHeap:
    pairs = load_keys(args.keys_file) if args.keys_file else synthetic(
        args.count, args.seed
    )
    heap = BinomialHeap()
    for key, value in pairs:
        heap.push(key, value)
    return heap


def _command_push(args: argparse.Namespace) -> int:
    heap = _heap(args)
    print(f"heap     {len(heap)} key(s), ranks {heap.shape()}, bits {bits(len(heap))}")
    for text in args.keys:
        try:
            edit = heap.push(int(text), text)
        except (ValueError, HeapError) as error:
            print(f"{text!r} is no key ({error})")
            return EXIT_UNUSABLE
        print(f"pushed   {text:>6}  {edit.line()}")
    return EXIT_OK if heap.invariant() else EXIT_NONE


def _command_pop(args: argparse.Namespace) -> int:
    heap = _heap(args)
    answer = EXIT_OK
    for _ in range(args.rounds if args.rounds is not None else len(heap)):
        try:
            key, value = heap.pop()
        except HeapError as error:
            print(f"drained  empty ({error})")
            answer = EXIT_NONE
            break
        print(f"popped   {describe(key)!r} = {value!r} ranks {heap.shape()}")
    return answer


def _command_meld(args: argparse.Namespace) -> int:
    left = _heap(args)
    right = BinomialHeap()
    for key in args.keys:
        try:
            right.push(int(key), key)
        except (ValueError, HeapError) as error:
            print(f"{key!r} is no key ({error})")
            return EXIT_UNUSABLE
    before = len(left)
    edit = left.meld(right)
    print(f"melded   {before} + {len(args.keys)} into {len(left)}")
    print(f"forest   ranks {left.shape()}, bits {bits(len(left))}, {edit.line()}")
    print(f"donor    {len(right)} key(s) left -- meld moved, never copied")
    return EXIT_OK if left.invariant() and not right else EXIT_NONE


def _command_size(args: argparse.Namespace) -> int:
    heap = _heap(args)
    print(f"size     {len(heap)}, bits {bits(len(heap))}, ranks {heap.shape()}")
    for line in heap.lines():
        print(line)
    stats = heap.stats()
    print(
        f"forest   {stats['trees']} tree(s) standing, {stats['links']} link(s)"
        f" spent, invariant {stats['invariant']}"
    )
    return EXIT_OK if stats["invariant"] else EXIT_NONE


def _command_peek(args: argparse.Namespace) -> int:
    heap = _heap(args)
    try:
        key, value = heap.peek()
    except HeapError as error:
        print(f"nothing  to peek ({error})")
        return EXIT_NONE
    print(f"peek     {key!r} = {value!r}, ranks {heap.shape()}")
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
        description="A mergeable integer min-heap of binomial trees.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser(
        "push", help="drop keys in and report the rank they reached"
    )
    push_parser.add_argument("--keys", dest="keys_file", default=None)
    push_parser.add_argument("--count", type=int, default=64)
    push_parser.add_argument("--seed", type=int, default=7)
    push_parser.add_argument("keys", nargs="+")
    push_parser.set_defaults(handler=_command_push)

    pop_parser = subparsers.add_parser(
        "pop", help="pop the minimum this many times, answers in order"
    )
    pop_parser.add_argument("--keys", dest="keys_file", default=None)
    pop_parser.add_argument("--seed", type=int, default=7)
    pop_parser.add_argument("--count", type=int, default=64)
    pop_parser.add_argument("rounds", nargs="?", type=int, default=None)
    pop_parser.set_defaults(handler=_command_pop)

    meld_parser = subparsers.add_parser(
        "meld", help="union a heap with fresh keys -- the product plain heaps refuse"
    )
    meld_parser.add_argument("--keys", dest="keys_file", default=None)
    meld_parser.add_argument("--count", type=int, default=64)
    meld_parser.add_argument("--seed", type=int, default=7)
    meld_parser.add_argument("keys", nargs="+")
    meld_parser.set_defaults(handler=_command_meld)

    size_parser = subparsers.add_parser(
        "size", help="the count, its bits, and the forest standing behind it"
    )
    size_parser.add_argument("--keys", dest="keys_file", default=None)
    size_parser.add_argument("--count", type=int, default=64)
    size_parser.add_argument("--seed", type=int, default=7)
    size_parser.set_defaults(handler=_command_size)

    peek_parser = subparsers.add_parser(
        "peek", help="the next pop, without paying for it"
    )
    peek_parser.add_argument("--keys", dest="keys_file", default=None)
    peek_parser.add_argument("--count", type=int, default=64)
    peek_parser.add_argument("--seed", type=int, default=7)
    peek_parser.set_defaults(handler=_command_peek)

    subparsers.add_parser("demo", help="six stories about forests and carries").set_defaults(
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
    except (StreamError, HeapError, KeyValueError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
