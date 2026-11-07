"""The command line: one question per run, keys in drain order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_keys
from .demo import stories
from .heap import HeapError, MinHeap
from .keys import KeysError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _heap(args: argparse.Namespace) -> MinHeap:  # type: ignore[no-untyped-def]
    return MinHeap(load_keys(args.keys))


def _payload(heap: MinHeap, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "keys": len(heap),
        "head": heap.peek() if heap else None,
        "array": heap.array(),
    }
    payload.update(extra)
    return payload


def _preview(keys: list[int], limit: int = 20) -> str:
    shown = keys[:limit]
    tail = "" if len(keys) <= limit else f", ... ({len(keys)} total)"
    return f"{shown}{tail}"


def _command_push(args: argparse.Namespace) -> int:
    heap = _heap(args)
    heap.push(args.key)
    if args.json:
        print(json.dumps(_payload(heap, {"seated": args.key}), indent=2))
    else:
        print(f"key        {args.key}")
        print(f"keys       {len(heap)}")
        print(f"head       {heap.peek()}")
        print(f"array      {_preview(heap.array())}")
    return EXIT_OK


def _command_pop(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if not heap:
        print("the heap is empty", file=sys.stderr)
        return EXIT_MISS
    top = heap.pop()
    if args.json:
        print(json.dumps(_payload(heap, {"popped": top}), indent=2))
    else:
        print(f"popped     {top}")
        print(f"keys       {len(heap)}")
        print(f"head       {heap.peek() if heap else 'None'}")
        print(f"array      {_preview(heap.array())}")
    return EXIT_OK


def _command_peek(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if not heap:
        print("the heap is empty", file=sys.stderr)
        return EXIT_MISS
    if args.json:
        print(json.dumps(_payload(heap, {"head": heap.peek()}), indent=2))
    else:
        print(f"head       {heap.peek()}")
        print(f"keys       {len(heap)}")
    return EXIT_OK


def _command_len(args: argparse.Namespace) -> int:
    heap = _heap(args)
    if args.json:
        print(json.dumps({"keys": len(heap), "array": heap.array()}, indent=2))
    else:
        print(f"keys       {len(heap)}")
        print(f"array      {_preview(heap.array())}")
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


def _key_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--keys", required=True, help="one key per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Integer keys, sifted by hand: push, pop, peek, len.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="seat a key, sift it up")
    _key_args(push_parser)
    push_parser.add_argument("key", type=int)
    push_parser.add_argument("--json", action="store_true")
    push_parser.set_defaults(handler=_command_push)

    pop_parser = subparsers.add_parser("pop", help="hand over the smallest key")
    _key_args(pop_parser)
    pop_parser.add_argument("--json", action="store_true")
    pop_parser.set_defaults(handler=_command_pop)

    peek_parser = subparsers.add_parser("peek", help="the smallest key, in place")
    _key_args(peek_parser)
    peek_parser.add_argument("--json", action="store_true")
    peek_parser.set_defaults(handler=_command_peek)

    len_parser = subparsers.add_parser("len", help="how many keys are seated")
    _key_args(len_parser)
    len_parser.add_argument("--json", action="store_true")
    len_parser.set_defaults(handler=_command_len)

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
