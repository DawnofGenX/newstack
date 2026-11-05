"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, demo
from .diff import diff, summary
from .patch import PatchError, TestFailed, apply, load
from .pointer import PointerError, parse, render, resolve

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(Exception):
    """The command line asked for something that cannot be answered."""


def _read_document(path: Path):
    try:
        return json.loads(path.read_text())
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not JSON: {error}") from error


def command_apply(args) -> int:
    document = _read_document(Path(args.document))
    operations = load(Path(args.patch))
    try:
        result = apply(document, operations)
    except TestFailed as error:
        print(f"refused      {error}", file=sys.stderr)
        return EXIT_REFUSED
    except PatchError as error:
        print(f"refused      {error}", file=sys.stderr)
        return EXIT_REFUSED
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"operations   {len(operations)}")
        for line in summary(operations):
            print(f"  {line}")
        print("result")
        print(json.dumps(result, indent=2, sort_keys=True))
    return EXIT_OK


def command_check(args) -> int:
    document = _read_document(Path(args.document))
    operations = load(Path(args.patch))
    try:
        apply(document, operations)
    except PatchError as error:
        print(f"refused      {error}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"applies      {len(operations)} operation(s), and the document is unchanged")
    return EXIT_OK


def command_resolve(args) -> int:
    document = _read_document(Path(args.document))
    parts = parse(args.pointer)
    try:
        value = resolve(document, parts)
    except PointerError as error:
        raise UsageError(str(error)) from error
    print(f"pointer      {render(parts) or '(root)'}")
    print(f"value        {json.dumps(value, sort_keys=True)}")
    return EXIT_OK


def command_diff(args) -> int:
    before = _read_document(Path(args.before))
    after = _read_document(Path(args.after))
    operations = diff(before, after)
    if args.json:
        print(json.dumps(operations, indent=2))
        return EXIT_OK
    print(f"operations   {len(operations)}")
    for line in summary(operations):
        print(f"  {line}")
    print(f"applies      {apply(before, operations) == after}")
    return EXIT_OK


def command_demo(args) -> int:
    sys.stdout.write(demo.render_stories())
    return EXIT_OK if all(story.held for story in demo.stories()) else EXIT_REFUSED


def command_selftest(args) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="JSON Pointer and JSON Patch you can watch"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply", help="apply a patch to a document")
    apply_parser.add_argument("--document", required=True)
    apply_parser.add_argument("--patch", required=True)
    apply_parser.add_argument("--json", action="store_true")
    apply_parser.set_defaults(handler=command_apply)

    check_parser = subparsers.add_parser("check", help="apply a patch and throw it away")
    check_parser.add_argument("--document", required=True)
    check_parser.add_argument("--patch", required=True)
    check_parser.set_defaults(handler=command_check)

    resolve_parser = subparsers.add_parser("resolve", help="read one pointer")
    resolve_parser.add_argument("--document", required=True)
    resolve_parser.add_argument("pointer")
    resolve_parser.set_defaults(handler=command_resolve)

    diff_parser = subparsers.add_parser("diff", help="print the patch between two documents")
    diff_parser.add_argument("--before", required=True)
    diff_parser.add_argument("--after", required=True)
    diff_parser.add_argument("--json", action="store_true")
    diff_parser.set_defaults(handler=command_diff)

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
    except (UsageError, PatchError, PointerError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
