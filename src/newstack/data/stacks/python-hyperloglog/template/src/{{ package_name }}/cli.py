"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, demo
from .hll import HyperLogLog, SketchError, parse_sketch, relative_error
from .measure import Comparison

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2


class UsageError(Exception):
    """The command line asked for something that cannot be answered."""


def load_sketch(path: str) -> HyperLogLog:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error}") from error
    try:
        return parse_sketch(payload)
    except SketchError as error:
        raise UsageError(f"{path}: {error}") from error


def save_sketch(sketch: HyperLogLog, path: str) -> None:
    text = json.dumps(sketch.as_dict(), indent=2, sort_keys=True) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def read_items(source: str) -> list[str]:
    if source == "-":
        return [line.rstrip("\n") for line in sys.stdin if line.strip()]
    try:
        text = Path(source).read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(f"cannot read {source}: {error}") from error
    return [line for line in text.splitlines() if line.strip()]


def command_build(args) -> int:
    items = read_items(args.input)
    sketch = HyperLogLog(args.precision)
    for item in items:
        sketch.add(item)
    save_sketch(sketch, args.sketch)
    print(f"built     {args.sketch}")
    print(f"items     {len(items)}")
    print(f"estimate  {sketch.count()}")
    promised = relative_error(sketch.precision) * 100
    print(f"promised  {promised:.2f}% at precision {sketch.precision}")
    return EXIT_OK


def command_estimate(args) -> int:
    sketch = load_sketch(args.sketch)
    count = sketch.count()
    promised = relative_error(sketch.precision)
    if args.json:
        print(json.dumps({"estimate": count, "precision": sketch.precision,
                          "promised": promised}, indent=2))
    else:
        print(f"distinct  ~{count}")
        print(f"promised  {promised * 100:.2f}%")
    if args.expect is None:
        return EXIT_OK
    comparison = Comparison(n=args.expect, estimate=count, bound=promised, sigma=0)
    if not args.json:
        print(f"error     {comparison.error * 100:+.2f}% against {args.expect}")
    return EXIT_OK if comparison.within else EXIT_BREACH


def command_merge(args) -> int:
    left = load_sketch(args.left)
    right = load_sketch(args.right)
    try:
        merged = left.merged(right)
    except SketchError as error:
        raise UsageError(str(error)) from error
    save_sketch(merged, args.out)
    print(f"merged    {args.out}")
    print(f"left      {left.count()}")
    print(f"right     {right.count()}")
    print(f"union     {merged.count()}")
    return EXIT_OK


def command_info(args) -> int:
    sketch = load_sketch(args.sketch)
    payload = {
        "precision": sketch.precision,
        "registers": sketch.size,
        "bytes": sketch.bytes_used,
        "zero_registers": sketch.zeros(),
        "adds": sketch.added,
        "registers_raised": sketch.raised,
        "estimate": sketch.count(),
        "promised": relative_error(sketch.precision),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"precision {sketch.precision}")
    print(f"registers {sketch.size} ({sketch.bytes_used} byte(s))")
    print(f"zeros     {sketch.zeros()}")
    print(f"adds      {sketch.added}")
    print(f"raised    {sketch.raised}")
    print(f"estimate  {sketch.count()}")
    print(f"promised  {relative_error(sketch.precision) * 100:.2f}%")
    return EXIT_OK


def command_demo(args) -> int:
    sys.stdout.write(demo.render())
    held = all(story.held for story in demo.stories())
    return EXIT_OK if held else EXIT_BREACH


def command_selftest(args) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description="estimate distinct counts")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build a sketch from items")
    build.add_argument("--input", default="-", help="file of one item per line, or - for stdin")
    build.add_argument("--sketch", required=True, help="where to write the sketch")
    build.add_argument("--precision", type=int, default=14)
    build.set_defaults(handler=command_build)

    estimate = subparsers.add_parser("estimate", help="report the estimate")
    estimate.add_argument("--sketch", required=True)
    estimate.add_argument("--expect", type=int, help="gate on the error against this count")
    estimate.add_argument("--json", action="store_true")
    estimate.set_defaults(handler=command_estimate)

    merge = subparsers.add_parser("merge", help="merge two sketches")
    merge.add_argument("--left", required=True)
    merge.add_argument("--right", required=True)
    merge.add_argument("--out", required=True)
    merge.set_defaults(handler=command_merge)

    info = subparsers.add_parser("info", help="describe a sketch")
    info.add_argument("--sketch", required=True)
    info.add_argument("--json", action="store_true")
    info.set_defaults(handler=command_info)

    demo_parser = subparsers.add_parser("demo", help="run the six stories")
    demo_parser.set_defaults(handler=command_demo)

    selftest_parser = subparsers.add_parser("selftest", help="run the built-in checks")
    selftest_parser.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except UsageError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except SketchError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
