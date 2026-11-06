"""The command line: parse, satisfy, intersect, sort, demo, selftest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo
from .explain import decide
from .ranges import RangeError, intersect, parse_range
from .version import Version, VersionError, parse

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """A command line that cannot be answered as written."""


def _arms_of(text: str) -> list[str]:
    chosen = parse_range(text)
    lines = [f"range      {chosen.text}", f"arms       {len(chosen.arms)}"]
    for number, arm in enumerate(chosen.arms, start=1):
        lines.append(f"  {number}. {arm.render()}")
    return lines


def _command_parse(args: argparse.Namespace) -> int:
    for line in _arms_of(args.range):
        print(line)
    return EXIT_OK


def _command_satisfy(args: argparse.Namespace) -> int:
    version = parse(args.version)
    chosen = parse_range(args.range)
    decision = decide(version, chosen)
    for line in decision.lines():
        print(line)
    if args.json:
        print(
            json.dumps(
                {
                    "version": str(version),
                    "range": chosen.text,
                    "satisfies": decision.ok,
                    "arm": decision.arm,
                    "reasons": list(decision.reasons),
                }
            )
        )
    return EXIT_OK if decision.ok else EXIT_NO_MATCH


def _command_intersect(args: argparse.Namespace) -> int:
    left = parse_range(args.left)
    right = parse_range(args.right)
    combined = intersect(left, right)
    if combined is None:
        print(f"left       {left.render()}")
        print(f"right      {right.render()}")
        print("verdict    empty: no version satisfies both")
        return EXIT_NO_MATCH
    print(f"left       {left.render()}")
    print(f"right      {right.render()}")
    for number, arm in enumerate(combined.arms, start=1):
        print(f"  {number}. {arm.render()}")
    print(f"verdict    {len(combined.arms)} arm(s)")
    return EXIT_OK


def _read_versions(path: Path) -> list[Version]:
    if not path.exists():
        raise UsageError(f"no such file: {path}")
    versions: list[Version] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        try:
            versions.append(parse(text))
        except VersionError as error:
            raise UsageError(f"line {number}: {error}") from error
    if not versions:
        raise UsageError(f"{path} holds no versions, and sorting nothing has no answer")
    return versions


def _command_sort(args: argparse.Namespace) -> int:
    versions = _read_versions(Path(args.input))
    ordered = sorted(versions)
    for version in ordered:
        print(version)
    if args.json:
        print(json.dumps([str(version) for version in ordered]))
    return EXIT_OK


def _command_demo(_: argparse.Namespace) -> int:
    return demo.run()


def _command_selftest(_: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Version ranges as a union of intervals you can check",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    parse_command = commands.add_parser("parse", help="read a range and print its arms")
    parse_command.add_argument("range")
    parse_command.set_defaults(handler=_command_parse)

    satisfy = commands.add_parser("satisfy", help="does a version satisfy a range?")
    satisfy.add_argument("version")
    satisfy.add_argument("--range", required=True, dest="range")
    satisfy.add_argument("--json", action="store_true")
    satisfy.set_defaults(handler=_command_satisfy)

    meet = commands.add_parser("intersect", help="the versions two ranges both allow")
    meet.add_argument("left")
    meet.add_argument("right")
    meet.set_defaults(handler=_command_intersect)

    sort = commands.add_parser("sort", help="order the versions in a file")
    sort.add_argument("--input", required=True)
    sort.add_argument("--json", action="store_true")
    sort.set_defaults(handler=_command_sort)

    demo_command = commands.add_parser("demo", help="the six stories")
    demo_command.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="check the library against itself")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (RangeError, VersionError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
