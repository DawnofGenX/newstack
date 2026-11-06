"""The command line: one question per run, and a report that names the spine."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_text
from .rope import Rope, RopeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _rope(args: argparse.Namespace) -> Rope:
    return Rope(load_text(args.text))


def _payload(rope: Rope, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "size": len(rope),
        "chunks": rope.leaf_count(),
        "height": rope.height(),
        "budget": rope.budget(),
        "balanced": rope.is_balanced(),
        "max_leaf": rope.max_leaf,
    }
    payload.update(extra)
    return payload


def _report(rope: Rope, text: str) -> None:
    print(f"size       {len(rope)} chars in {rope.leaf_count()} chunk(s)")
    print(f"spine      height {rope.height()}, budget {rope.budget()}")
    print(f"balanced   {rope.is_balanced()}")
    print(f"text       {text}")


def _command_load(args: argparse.Namespace) -> int:
    rope = _rope(args)
    if args.json:
        print(json.dumps(_payload(rope, {"text": rope.to_string()}), indent=2))
        return EXIT_OK
    _report(rope, rope.to_string())
    return EXIT_OK


def _command_slice(args: argparse.Namespace) -> int:
    rope = _rope(args)
    if args.stop < args.start:
        raise UsageError(f"{args.stop} sits below {args.start}, a window cannot close down")
    window = rope.slice(args.start, args.stop)
    if args.json:
        payload = _payload(window, {"window": [args.start, args.stop], "text": window.to_string()})
        print(json.dumps(payload, indent=2))
    else:
        print(f"window     [{args.start}..{args.stop})")
        _report(window, window.to_string())
    return EXIT_OK if len(window) else EXIT_NONE


def _command_join(args: argparse.Namespace) -> int:
    first = Rope(load_text(args.text))
    second = Rope(load_text(args.other))
    joined = first.concat(second)
    if args.json:
        payload = _payload(joined, {"text": joined.to_string()})
        print(json.dumps(payload, indent=2))
    else:
        print(f"ropes      {args.text} + {args.other}")
        _report(joined, joined.to_string())
    return EXIT_OK


def _command_split(args: argparse.Namespace) -> int:
    rope = _rope(args)
    left, right = rope.split(args.at)
    joined = left.concat(right)
    if args.json:
        extra = {
            "left": left.to_string(),
            "right": right.to_string(),
            "rejoined": joined.to_string() == rope.to_string(),
        }
        print(json.dumps(_payload(joined, extra), indent=2))
    else:
        print(f"at         {args.at}")
        print(f"left       {left.to_string()}")
        print(f"right      {right.to_string()}")
        print(f"rejoined   {joined.to_string() == rope.to_string()}")
    return EXIT_OK if joined.to_string() == rope.to_string() else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A rope of cached-length chunks: slice, edit, join, split.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="read a text and show its spine")
    _text_args(load_parser)
    load_parser.add_argument("--json", action="store_true")
    load_parser.set_defaults(handler=_command_load)

    slice_parser = subparsers.add_parser("slice", help="a window as a rope")
    _text_args(slice_parser)
    slice_parser.add_argument("--start", type=int, required=True)
    slice_parser.add_argument("--stop", type=int, required=True)
    slice_parser.add_argument("--json", action="store_true")
    slice_parser.set_defaults(handler=_command_slice)

    join_parser = subparsers.add_parser("join", help="concat two texts, no copying")
    _text_args(join_parser)
    join_parser.add_argument("--other", required=True, help="the second text")
    join_parser.add_argument("--json", action="store_true")
    join_parser.set_defaults(handler=_command_join)

    split_parser = subparsers.add_parser(
        "split", help="cut at an offset, concat back, compare"
    )
    _text_args(split_parser)
    split_parser.add_argument("--at", type=int, required=True)
    split_parser.add_argument("--json", action="store_true")
    split_parser.set_defaults(handler=_command_split)

    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def _text_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", required=True, help="a text document")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (RopeError, CorpusError, UsageError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
