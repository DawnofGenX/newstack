"""The command line: diff two files, apply a patch, and check the round trip."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from . import demo
from .apply import apply_text
from .diff import diff_text, format_patch, parse_patch
from .model import CONTEXT, DiffError, FilePatch
from .verify import roundtrip

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_UNUSABLE = 2


def read_text(path: Path) -> str:
    """Read bytes and decode: text mode would translate CRLF and hide the endings."""
    try:
        data = path.read_bytes()
    except OSError as error:
        raise DiffError(f"cannot read {path}: {error.strerror or error}") from error
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DiffError(f"{path} is not UTF-8: {error}") from error


def write_text(path: Path, text: str) -> None:
    try:
        path.write_bytes(text.encode("utf-8"))
    except OSError as error:
        raise DiffError(f"cannot write {path}: {error.strerror or error}") from error


def command_diff(args: argparse.Namespace) -> int:
    patch: FilePatch = diff_text(read_text(args.old), read_text(args.new), args.context)
    patch = replace(patch, old_path=str(args.old), new_path=str(args.new))
    if not patch.hunks:
        print(f"identical  {args.old} and {args.new} have no differences", file=sys.stderr)
        return EXIT_OK
    text = format_patch(patch)
    if args.out is not None:
        write_text(args.out, text)
        print(f"wrote      {args.out}: {patch.line()}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return EXIT_OK


def command_apply(args: argparse.Namespace) -> int:
    patch = parse_patch(read_text(args.patch))
    original = read_text(args.file)
    applied = apply_text(original, patch, fuzz=args.fuzz)
    print(f"{applied.line()}", file=sys.stderr)
    if args.in_place:
        write_text(args.file, applied.text)
        print(f"wrote      {args.file}", file=sys.stderr)
    else:
        sys.stdout.write(applied.text)
    return EXIT_OK


def command_check(args: argparse.Namespace) -> int:
    verdict = roundtrip(read_text(args.old), read_text(args.new), args.context)
    for line in verdict.lines():
        print(line)
    print(f"verdict   {'all three claims hold' if verdict.ok else 'a claim broke'}")
    return EXIT_OK if verdict.ok else EXIT_MISMATCH


def command_demo(_args: argparse.Namespace) -> int:
    steps = demo.run()
    print(demo.render(steps))
    return EXIT_OK if all(step.ok for step in steps) else EXIT_MISMATCH


def command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__)
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    differ = sub.add_parser("diff", help="print a unified diff of two files")
    differ.add_argument("old", type=Path)
    differ.add_argument("new", type=Path)
    differ.add_argument("--context", type=int, default=CONTEXT)
    differ.add_argument("-o", "--out", type=Path, default=None)
    differ.set_defaults(handler=command_diff)

    applier = sub.add_parser("apply", help="apply a patch to a file")
    applier.add_argument("file", type=Path)
    applier.add_argument("patch", type=Path)
    applier.add_argument("--fuzz", type=int, default=0)
    applier.add_argument("-i", "--in-place", action="store_true")
    applier.set_defaults(handler=command_apply)

    checker = sub.add_parser("check", help="diff, apply, and diff again")
    checker.add_argument("old", type=Path)
    checker.add_argument("new", type=Path)
    checker.add_argument("--context", type=int, default=CONTEXT)
    checker.set_defaults(handler=command_check)

    shower = sub.add_parser("demo", help="run the seven scenarios")
    shower.set_defaults(handler=command_demo)

    test = sub.add_parser("selftest", help="check this build against itself")
    test.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except DiffError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (OSError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
