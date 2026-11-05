"""Command line entry point: fold readings, merge rollups, show the arithmetic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo, merge, model, rollup, selftest

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_UNUSABLE = 2
DEFAULT_WIDTH = 60.0


def _readings(path: Path) -> list[model.Sample]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise model.RollupError(f"cannot read {path}: {error.strerror or error}") from None
    readings: list[model.Sample] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        readings.append(rollup.parse_line(number, line))
    if not readings:
        raise model.RollupError(f"{path} holds no readings; a rate needs at least two")
    return readings


def _rows(pieces: list[model.Rollup]) -> list[str]:
    return [model.HEADER, *(piece.line() for piece in pieces)]


def command_rollup(_: argparse.Namespace, args: argparse.Namespace) -> int:
    width_us = model.seconds(args.width)
    readings = _readings(args.file)
    pieces = rollup.rollup(readings, width_us, name=args.name, shard=args.shard)
    holes = rollup.gaps(pieces, width_us)
    rate = rollup.rate_per_second(pieces)
    if args.json:
        print(
            json.dumps(
                {
                    "width_us": width_us,
                    "rollups": [piece.as_dict() for piece in pieces],
                    "gaps": [hole.start_us for hole in holes],
                    "rate_per_second": round(rate, 6),
                },
                indent=2,
            )
        )
    else:
        for line in _rows(pieces):
            print(line)
        covered = sum(piece.covered_us for piece in pieces)
        print(
            f"windows  {len(pieces)} with readings, {len(holes)} without; "
            f"{covered / model.MICROSECONDS:.3f}s observed"
        )
        print(f"rate     {rate:.3f}/s over the windows that were actually measured")
        for hole in holes:
            print(
                f"gap      window {hole.start_us}..{hole.end_us} has no reading; "
                "that window is unknown, not zero"
            )
    return EXIT_PROBLEM if holes else EXIT_OK


def command_merge(_: argparse.Namespace, args: argparse.Namespace) -> int:
    delivered: list[model.Rollup] = []
    for path in args.files:
        delivered.extend(merge.load(path))
    result = merge.merge(delivered)
    combined = merge.combine(result.rollups)
    if args.json:
        print(
            json.dumps(
                {
                    "rollups": [piece.as_dict() for piece in result.rollups],
                    "repeated": result.repeated,
                    "combined": [piece.as_dict() for piece in combined],
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(f"merged   {len(result.rollups)} window(s), {result.repeated} repeat(s) dropped")
    for line in _rows(result.rollups):
        print(line)
    print("combined across shards")
    for line in _rows(combined):
        print(line)
    return EXIT_OK


def command_demo(_: argparse.Namespace, args: argparse.Namespace) -> int:
    steps = demo.run()
    print(demo.render(steps) if not args.json else json.dumps(demo.payload(steps), indent=2))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_PROBLEM


def command_selftest(_: argparse.Namespace, args: argparse.Namespace) -> int:
    passed, total = selftest.run()
    print(f"selftest: {passed} checks passed, {total - passed} failed out of {total}")
    return EXIT_OK if passed == total else EXIT_PROBLEM


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Turn counter readings into windows you can defend."
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    folder = subparsers.add_parser("rollup", help="fold a JSONL file of readings into windows")
    folder.add_argument("--file", type=Path, required=True, help="one reading per line")
    folder.add_argument(
        "--width", type=float, default=DEFAULT_WIDTH, help="window width in seconds"
    )
    folder.add_argument("--name", default="counter", help="what is being counted")
    folder.add_argument("--shard", default="default", help="which shard produced the readings")
    folder.add_argument("--json", action="store_true")
    folder.set_defaults(handler=command_rollup)

    merger = subparsers.add_parser("merge", help="merge rollup files that may repeat")
    merger.add_argument("files", type=Path, nargs="+")
    merger.add_argument("--json", action="store_true")
    merger.set_defaults(handler=command_merge)

    shower = subparsers.add_parser("demo", help="four scenarios about what a number can answer")
    shower.add_argument("--json", action="store_true")
    shower.set_defaults(handler=command_demo)

    tester = subparsers.add_parser("selftest", help="check the arithmetic without pytest")
    tester.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(None, args))
    except (model.RollupError, ValueError, TypeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
