"""The command line: one question per run, counts in ledger order."""

from __future__ import annotations

import argparse
import json
import sys

from .corpus import CorpusError, load_stream, synthetic
from .demo import stories
from .keys import KeysError
from .selftest import run as run_selftest
from .sketch import CountMinSketch, SketchError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _sketch(args: argparse.Namespace) -> CountMinSketch:
    sketch = CountMinSketch()
    for key, n in load_stream(args.stream):
        sketch.add(key, n)
    return sketch


def _command_add(args: argparse.Namespace) -> int:
    sketch = _sketch(args)
    sketch.add(args.key, args.n)
    if args.json:
        print(json.dumps({
            "key": args.key,
            "count": sketch.count(args.key),
            "tracked": len(sketch.keys()),
            "total": sketch.total,
        }, indent=2))
    else:
        print(f"key        {args.key}")
        print(f"count      {sketch.count(args.key)}")
        print(f"tracked    {len(sketch.keys())}")
        print(f"total      {sketch.total}")
    return EXIT_OK


def _command_count(args: argparse.Namespace) -> int:
    sketch = _sketch(args)
    answer = sketch.count(args.key)
    tracked = args.key in sketch
    if args.json:
        print(json.dumps({
            "key": args.key,
            "count": answer,
            "tracked": tracked,
            "cells": sketch.cells_of(args.key),
        }, indent=2))
    else:
        print(f"key        {args.key}")
        print(f"count      {answer}")
        print(f"tracked    {tracked}")
    return EXIT_OK if tracked else EXIT_MISS


def _command_report(args: argparse.Namespace) -> int:
    sketch = _sketch(args)
    drift = sum(
        1 for key in sorted(sketch) if sketch.count(key) != sketch.true_count(key)
    )
    if args.json:
        payload = sketch.report()
        payload["drift"] = drift
        print(json.dumps(payload, indent=2))
    else:
        for name, value in (
            ("width", sketch.width),
            ("depth", sketch.depth),
            ("rows", ",".join(str(m) for m in sketch.multipliers)),
            ("tracked", len(sketch.keys())),
            ("total", sketch.total),
            ("drift", drift),
        ):
            print(f"{name:<10} {value}")
    return EXIT_OK


def _command_seed(args: argparse.Namespace) -> int:
    events = synthetic(args.count, seed=args.seed)
    for key, n in events:
        print(f"{key} {n}")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    report = run_selftest()
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


def _stream_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stream", required=True, help="one 'key n' per line")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Counts on [0, 256): add, count, report, seed, selftest, demo.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="seat n more for a key")
    _stream_args(add_parser)
    add_parser.add_argument("key", type=int)
    add_parser.add_argument("n", type=int, nargs="?", default=1)
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    count_parser = subparsers.add_parser("count", help="the min of the rows")
    _stream_args(count_parser)
    count_parser.add_argument("key", type=int)
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=_command_count)

    report_parser = subparsers.add_parser("report", help="the grid and its drift")
    _stream_args(report_parser)
    report_parser.add_argument("--json", action="store_true")
    report_parser.set_defaults(handler=_command_report)

    seed_parser = subparsers.add_parser("seed", help="a deterministic stream")
    seed_parser.add_argument("--count", type=int, default=16)
    seed_parser.add_argument("--seed", type=int, default=20261107)
    seed_parser.set_defaults(handler=_command_seed)

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
    except (CorpusError, KeysError, SketchError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
