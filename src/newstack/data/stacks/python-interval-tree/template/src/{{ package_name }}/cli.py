"""The command line: one question per run, and answers in start order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_spans
from .span import SpanError
from .tree import IntervalTree, TreeError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


def _tree(args: argparse.Namespace) -> IntervalTree:
    return IntervalTree(load_spans(args.intervals))


def _payload(tree: IntervalTree, extra: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {
        "spans": len(tree),
        "height": tree.height,
        "corpus": [span.display() for span in tree.walk()],
    }
    payload.update(extra)
    return payload


def _render(spans: list) -> list[str]:
    return [f"  {span.display()}" for span in spans]


def _command_load(args: argparse.Namespace) -> int:
    tree = _tree(args)
    if args.json:
        print(json.dumps(_payload(tree, {}), indent=2))
        return EXIT_OK
    print(f"spans      {len(tree)} held, height {tree.height}")
    for line in _render(tree.walk()):
        print(line)
    return EXIT_OK


def _command_stab(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.stab(args.point)
    if args.json:
        payload = _payload(tree, {"point": args.point, "count": len(found)})
        print(json.dumps(payload, indent=2))
    else:
        print(f"point      {args.point}")
        print(f"held       {len(found)} span(s)")
        for line in _render(found):
            print(line)
    return EXIT_OK if found else EXIT_NONE


def _command_overlap(args: argparse.Namespace) -> int:
    tree = _tree(args)
    found = tree.overlap(args.low, args.high)
    if args.json:
        payload = _payload(tree, {"window": [args.low, args.high], "count": len(found)})
        print(json.dumps(payload, indent=2))
    else:
        print(f"window     [{args.low}..{args.high})")
        print(f"touched    {len(found)} span(s)")
        for line in _render(found):
            print(line)
    return EXIT_OK if found else EXIT_NONE


def _command_first(args: argparse.Namespace) -> int:
    tree = _tree(args)
    winner = tree.first(args.point)
    if args.json:
        payload = _payload(tree, {"point": args.point})
        payload["first"] = winner.display() if winner else None
        print(json.dumps(payload, indent=2))
    else:
        print(f"point      {args.point}")
        print(f"first      {winner.display() if winner else 'nothing'}")
    return EXIT_OK if winner else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def _corpus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--intervals", required=True, help="start end per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A centered interval tree over half-open spans: stab, overlap, first.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser("load", help="build the tree and walk it in order")
    _corpus_args(load_parser)
    load_parser.add_argument("--json", action="store_true")
    load_parser.set_defaults(handler=_command_load)

    stab_parser = subparsers.add_parser("stab", help="every span holding one point")
    _corpus_args(stab_parser)
    stab_parser.add_argument("--point", type=int, required=True)
    stab_parser.add_argument("--json", action="store_true")
    stab_parser.set_defaults(handler=_command_stab)

    overlap_parser = subparsers.add_parser(
        "overlap", help="every span touching a half-open window"
    )
    _corpus_args(overlap_parser)
    overlap_parser.add_argument("--low", type=int, required=True)
    overlap_parser.add_argument("--high", type=int, required=True)
    overlap_parser.add_argument("--json", action="store_true")
    overlap_parser.set_defaults(handler=_command_overlap)

    first_parser = subparsers.add_parser("first", help="the earliest span holding a point")
    _corpus_args(first_parser)
    first_parser.add_argument("--point", type=int, required=True)
    first_parser.add_argument("--json", action="store_true")
    first_parser.set_defaults(handler=_command_first)

    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (TreeError, SpanError, CorpusError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
