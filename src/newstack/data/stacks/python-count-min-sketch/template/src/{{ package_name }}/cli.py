"""Command line: build a sketch from items and read estimates out of it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .sketch import CountMinSketch, SketchError, epsilon, parse_sketch

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line does not describe a sketch operation we can perform."""


def read_sketch(path: Path) -> CountMinSketch:
    if not path.exists():
        raise UsageError(f"{path} does not exist; create it with `{PROGRAM} add --sketch {path}`")
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error}") from error
    return parse_sketch(payload)


def write_sketch(path: Path, sketch: CountMinSketch) -> None:
    path.write_text(json.dumps(sketch.as_dict(), indent=2) + "\n")


def command_demo(args: argparse.Namespace) -> int:
    from .demo import render

    sys.stdout.write(render())
    return EXIT_OK


def command_add(args: argparse.Namespace) -> int:
    if args.sketch.exists():
        sketch = read_sketch(args.sketch)
    else:
        sketch = CountMinSketch(args.width, args.depth, conservative=args.conservative)
    for item in args.items:
        sketch.add(item, args.count)
    write_sketch(args.sketch, sketch)
    print(
        f"added {args.count} x {len(args.items)} item(s); the sketch holds "
        f"{sketch.total} updates over {sketch.width}x{sketch.depth} counters"
    )
    return EXIT_OK


def command_estimate(args: argparse.Namespace) -> int:
    sketch = read_sketch(args.sketch)
    estimate = sketch.estimate(args.item)
    if args.json:
        print(json.dumps({"item": args.item, "estimate": estimate, "bound": sketch.bound()}))
        return EXIT_OK
    print(f"{args.item}  {estimate}")
    print(
        f"  every estimate for this sketch can be at most "
        f"{epsilon(sketch.width) * sketch.total:.1f} above the truth"
    )
    return EXIT_OK


def command_info(args: argparse.Namespace) -> int:
    sketch = read_sketch(args.sketch)
    if args.json:
        print(json.dumps({**sketch.as_dict(), "error_bound": sketch.bound()}, indent=2))
        return EXIT_OK
    print(f"width        {sketch.width}")
    print(f"depth        {sketch.depth}")
    print(f"conservative {sketch.conservative}")
    print(f"updates      {sketch.total}")
    print(f"calls        {sketch.updates}")
    print(f"promise      {sketch.bound():.1f} (e/width of the updates)")
    return EXIT_OK


def command_merge(args: argparse.Namespace) -> int:
    left = read_sketch(args.left)
    right = read_sketch(args.right)
    merged = left.merge(right)
    write_sketch(args.out, merged)
    print(
        f"merged {left.total} and {right.total} updates into {args.out}; "
        f"the rows add pointwise, so the union is exact"
    )
    return EXIT_OK


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="count-min sketch: an estimate with a stated error"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="six stories about estimates")
    demo.set_defaults(func=command_demo)

    add = sub.add_parser("add", help="add items to a sketch, creating it if needed")
    add.add_argument("--sketch", type=Path, required=True)
    add.add_argument("--items", nargs="+", required=True)
    add.add_argument("--count", type=int, default=1)
    add.add_argument("--width", type=int, default=2048)
    add.add_argument("--depth", type=int, default=5)
    add.add_argument("--conservative", action="store_true")
    add.set_defaults(func=command_add)

    estimate = sub.add_parser("estimate", help="read one item's estimate")
    estimate.add_argument("--sketch", type=Path, required=True)
    estimate.add_argument("--item", required=True)
    estimate.add_argument("--json", action="store_true")
    estimate.set_defaults(func=command_estimate)

    info = sub.add_parser("info", help="describe a sketch")
    info.add_argument("--sketch", type=Path, required=True)
    info.add_argument("--json", action="store_true")
    info.set_defaults(func=command_info)

    merge = sub.add_parser("merge", help="add two sketches pointwise")
    merge.add_argument("--left", type=Path, required=True)
    merge.add_argument("--right", type=Path, required=True)
    merge.add_argument("--out", type=Path, required=True)
    merge.set_defaults(func=command_merge)

    selftest = sub.add_parser("selftest", help="check the invariants")
    selftest.set_defaults(func=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except (UsageError, SketchError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
