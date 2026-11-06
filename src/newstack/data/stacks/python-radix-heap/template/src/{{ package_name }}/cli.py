"""The command line: a heap per run, and a report that shows its buckets."""

from __future__ import annotations

import argparse
import sys

from .heap import BUCKETS, HeapError, RadixHeap
from .keys import KeyValueError, describe
from .streams import StreamError, load_keys, synthetic

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _heap(args: argparse.Namespace) -> RadixHeap:
    pairs = load_keys(args.keys_file) if args.keys_file else synthetic(
        args.count, args.seed
    )
    heap = RadixHeap()
    for key, value in pairs:
        heap.push(key, value)
    return heap


def _command_build(args: argparse.Namespace) -> int:
    heap = _heap(args)
    for line in heap.lines():
        print(line)
    stats = heap.stats()
    print(
        f"window   {stats['nonzero']} of {BUCKETS} buckets hold keys,"
        f" invariant {stats['invariant']}"
    )
    return EXIT_OK


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
        print(f"popped   {describe(key)!r} = {value!r} base {heap.base}")
    return answer


def _command_push(args: argparse.Namespace) -> int:
    heap = _heap(args)
    print(f"heap     {len(heap)} key(s), base {heap.base}")
    for text in args.keys:
        try:
            edit = heap.push(int(text), text)
        except (ValueError, HeapError) as error:
            print(f"{text!r} is no key ({error})")
            return EXIT_UNUSABLE
        print(f"pushed   {text:>6}  {edit.line()}")
    return EXIT_OK if heap.invariant() else EXIT_NONE


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
        description="An integer min-heap whose buckets follow the keys' bits.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build", help="load a heap and print where the keys sit"
    )
    build_parser_.add_argument("--keys", dest="keys_file", default=None)
    build_parser_.add_argument("--count", type=int, default=64)
    build_parser_.add_argument("--seed", type=int, default=7)
    build_parser_.set_defaults(handler=_command_build)

    pop_parser = subparsers.add_parser(
        "pop", help="pop the minimum this many times, answers in order"
    )
    pop_parser.add_argument("--keys", dest="keys_file", default=None)
    pop_parser.add_argument("--seed", type=int, default=7)
    pop_parser.add_argument("--count", type=int, default=64)
    pop_parser.add_argument("rounds", nargs="?", type=int, default=None)
    pop_parser.set_defaults(handler=_command_pop)

    push_parser = subparsers.add_parser(
        "push", help="drop keys into the buckets and report where they sat"
    )
    push_parser.add_argument("--keys", dest="keys_file", default=None)
    push_parser.add_argument("--count", type=int, default=64)
    push_parser.add_argument("--seed", type=int, default=7)
    push_parser.add_argument("keys", nargs="+")
    push_parser.set_defaults(handler=_command_push)

    subparsers.add_parser("demo", help="six stories about buckets and bits").set_defaults(
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
