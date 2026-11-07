"""The command line: one question per run, keys in heap order.

The item list ranks the heap; decrease-key targets are tracked by
the handle push hands back, and the CLI maps a 1-based item number
to the handle of that list position.
"""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_items
from .demo import stories
from .heap import FibonacciHeap, HeapError
from .keys import KeysError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _heap(args: argparse.Namespace) -> FibonacciHeap:  # type: ignore[no-untyped-def]
    return FibonacciHeap(load_items(args.items))


def _payload(heap: FibonacciHeap, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "items": len(heap),
        "min": heap.peek() if len(heap) else None,
        "keys": heap.keys(),
        "audit": heap.audit(),
    }
    payload.update(extra)
    return payload


def _preview(keys: list[int], limit: int = 20) -> str:
    shown = keys[:limit]
    tail = "" if len(keys) <= limit else f", ... ({len(keys)} total)"
    return f"{shown}{tail}"


def _command_push(args: argparse.Namespace) -> int:
    heap = _heap(args)
    handle = heap.push(args.key)
    if args.json:
        print(json.dumps(_payload(heap, {"item": handle.token}), indent=2))
    else:
        print(f"item       {handle.token}")
        print(f"key        {args.key}")
        print(f"items      {len(heap)}")
        print(f"min        {heap.peek()}")
    return EXIT_OK


def _command_pop(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if not len(heap):
        print("the heap is empty", file=sys.stderr)
        return EXIT_MISS
    released = heap.pop_min()
    if args.json:
        print(json.dumps(_payload(heap, {"released": released}), indent=2))
    else:
        print(f"released   {released}")
        print(f"items      {len(heap)}")
        print(f"keys       {_preview(heap.keys())}")
    return EXIT_OK


def _command_peek(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if not len(heap):
        print("the heap is empty", file=sys.stderr)
        return EXIT_MISS
    if args.json:
        print(json.dumps(_payload(heap, {"min": heap.peek()}), indent=2))
    else:
        print(f"min        {heap.peek()}")
        print(f"items      {len(heap)}")
    return EXIT_OK


def _command_size(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if args.json:
        print(json.dumps(_payload(heap, {}), indent=2))
    else:
        print(f"items      {len(heap)}")
        print(f"keys       {_preview(heap.keys())}")
    return EXIT_OK if len(heap) else EXIT_MISS


def _command_decrease(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if not 1 <= args.item <= len(heap):
        print(f"no item {args.item} in a heap of {len(heap)}", file=sys.stderr)
        return EXIT_UNUSABLE
    handle = heap._handles[args.item]
    heap.decrease(handle, args.key)
    if args.json:
        print(json.dumps(_payload(heap, {"item": args.item, "key": args.key}), indent=2))
    else:
        print(f"item       {args.item}")
        print(f"key        {args.key}")
        print(f"min        {heap.peek()}")
        print(f"keys       {_preview(heap.keys())}")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_MISS


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_MISS


def _item_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--items", required=True, help="one key per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Integer keys, forest-ordered: push, pop, decrease, peek, size.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="seat an item, get a handle")
    _item_args(push_parser)
    push_parser.add_argument("key", type=int)
    push_parser.add_argument("--json", action="store_true")
    push_parser.set_defaults(handler=_command_push)

    pop_parser = subparsers.add_parser("pop", help="release the smallest key")
    _item_args(pop_parser)
    pop_parser.add_argument("--json", action="store_true")
    pop_parser.set_defaults(handler=_command_pop)

    peek_parser = subparsers.add_parser("peek", help="the next release")
    _item_args(peek_parser)
    peek_parser.add_argument("--json", action="store_true")
    peek_parser.set_defaults(handler=_command_peek)

    size_parser = subparsers.add_parser("size", help="live items and live keys")
    _item_args(size_parser)
    size_parser.add_argument("--json", action="store_true")
    size_parser.set_defaults(handler=_command_size)

    decrease_parser = subparsers.add_parser("decrease", help="drop a tracked item")
    _item_args(decrease_parser)
    decrease_parser.add_argument("item", type=int, help="1-based item number")
    decrease_parser.add_argument("key", type=int)
    decrease_parser.add_argument("--json", action="store_true")
    decrease_parser.set_defaults(handler=_command_decrease)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="six stories, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (CorpusError, KeysError, HeapError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
