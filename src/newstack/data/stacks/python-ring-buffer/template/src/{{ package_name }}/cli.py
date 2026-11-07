"""The command line: one question per run, values in drain order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_values
from .demo import stories
from .ring import RingBuffer, RingError
from .storm import StormError
from .values import ValuesError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
DEFAULT_CAPACITY = 8

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _buffer(args: argparse.Namespace) -> RingBuffer:  # type: ignore[no-untyped-def]
    return RingBuffer(args.capacity, load_values(args.values))


def _payload(ring: RingBuffer, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "capacity": ring.capacity,
        "count": len(ring),
        "head": ring.head,
        "contents": list(ring.contents()),
    }
    payload.update(extra)
    return payload


def _preview(values: tuple[int, ...], limit: int = 20) -> str:
    shown = list(values[:limit])
    tail = "" if len(values) <= limit else f", ... ({len(values)} total)"
    return f"{shown}{tail}"


def _command_push(args: argparse.Namespace) -> int:
    ring = _buffer(args)
    dropped = ring.push(args.value)
    if args.json:
        print(json.dumps(_payload(ring, {"pushed": args.value, "dropped": dropped}), indent=2))
    else:
        print(f"pushed     {args.value}")
        print(f"dropped    {dropped}")
        print(f"count      {len(ring)}")
        print(f"contents   {_preview(ring.contents())}")
    return EXIT_OK


def _command_pop(args: argparse.Namespace) -> int:
    ring = _buffer(args)
    if not len(ring):
        if args.json:
            print(json.dumps(_payload(ring, {"popped": None}), indent=2))
        print("popped     None")
        return EXIT_MISS
    value = ring.pop()
    if args.json:
        print(json.dumps(_payload(ring, {"popped": value}), indent=2))
    else:
        print(f"popped     {value}")
        print(f"count      {len(ring)}")
        print(f"contents   {_preview(ring.contents())}")
    return EXIT_OK


def _command_peek(args: argparse.Namespace) -> int:
    ring = _buffer(args)
    if not len(ring):
        if args.json:
            print(json.dumps(_payload(ring, {"oldest": None}), indent=2))
        print("oldest     None")
        return EXIT_MISS
    value = ring.peek()
    if args.json:
        print(json.dumps(_payload(ring, {"oldest": value}), indent=2))
    else:
        print(f"oldest     {value}")
        print(f"count      {len(ring)}")
    return EXIT_OK


def _command_drain(args: argparse.Namespace) -> int:
    ring = _buffer(args)
    seen = ring.drain()
    if args.json:
        print(json.dumps({"capacity": ring.capacity, "drained": seen}, indent=2))
    else:
        print(f"drained    {len(seen)}")
        for value in seen:
            print(f"  {value}")
    return EXIT_OK if seen else EXIT_MISS


def _command_count(args: argparse.Namespace) -> int:
    ring = _buffer(args)
    if args.json:
        print(json.dumps(_payload(ring, {}), indent=2))
    else:
        print(f"capacity   {ring.capacity}")
        print(f"count      {len(ring)}")
        print(f"head       {ring.head}")
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


def _seat_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--values", required=True, help="one value per line")
    parser.add_argument("--capacity", type=int, default=DEFAULT_CAPACITY)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Integer values, fixed slots: push, pop, peek, drain, count.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="seat a value")
    _seat_args(push_parser)
    push_parser.add_argument("value", type=int)
    push_parser.add_argument("--json", action="store_true")
    push_parser.set_defaults(handler=_command_push)

    pop_parser = subparsers.add_parser("pop", help="hand back the oldest")
    _seat_args(pop_parser)
    pop_parser.add_argument("--json", action="store_true")
    pop_parser.set_defaults(handler=_command_pop)

    peek_parser = subparsers.add_parser("peek", help="the oldest, unmoved")
    _seat_args(peek_parser)
    peek_parser.add_argument("--json", action="store_true")
    peek_parser.set_defaults(handler=_command_peek)

    drain_parser = subparsers.add_parser("drain", help="everything, in order")
    _seat_args(drain_parser)
    drain_parser.add_argument("--json", action="store_true")
    drain_parser.set_defaults(handler=_command_drain)

    count_parser = subparsers.add_parser("count", help="capacity and count")
    _seat_args(count_parser)
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

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
    except (CorpusError, ValuesError, RingError, StormError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
