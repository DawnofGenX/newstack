"""Command line for the three-way merge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo as demo_module
from .merge import STYLES, MergeError, MergeResult, merge_files

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_CONFLICT = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line asked for something it cannot do."""


def _labels(text: str | None) -> tuple[str, str]:
    if text is None:
        return ("ours", "theirs")
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2 or not all(parts):
        raise UsageError('--labels takes two names separated by a comma, like "ours,theirs"')
    return (parts[0], parts[1])


def _payload(result: MergeResult) -> dict[str, object]:
    return {
        "clean": result.clean,
        "conflicts": result.conflicts,
        "agreed": result.agreed,
        "chunks": len(result.chunks),
        "changes": {"ours": len(result.ours_changes), "theirs": len(result.theirs_changes)},
        "text": result.text,
    }


def _command_merge(args: argparse.Namespace) -> int:
    result = merge_files(
        args.base, args.ours, args.theirs, labels=_labels(args.labels), style=args.style
    )
    if args.json:
        print(json.dumps(_payload(result), indent=2))
    elif args.out:
        Path(args.out).write_text(result.text, encoding="utf-8")
        print(f"wrote      {Path(args.out)}", file=sys.stderr)
    else:
        sys.stdout.write(result.text)
        sys.stdout.flush()
    if not args.quiet:
        print(f"merge      {result.summary()}", file=sys.stderr)
    return EXIT_OK if result.clean else EXIT_CONFLICT


def _command_explain(args: argparse.Namespace) -> int:
    result = merge_files(
        args.base, args.ours, args.theirs, labels=_labels(args.labels), style=args.style
    )
    print(f"merge      {result.summary()}")
    for line in result.lines():
        print(line)
    print("")
    sys.stdout.write(result.text)
    return EXIT_OK if result.clean else EXIT_CONFLICT


def _command_demo(_args: argparse.Namespace) -> int:
    lines = demo_module.render_stories()
    for line in lines:
        print(line)
    return EXIT_OK if lines[-1].startswith("stories      6 of 6") else EXIT_CONFLICT


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import main as selftest_main

    return selftest_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Merge two edits of one base, and say what could not be decided.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    def inputs(target: argparse.ArgumentParser) -> None:
        target.add_argument("--base", required=True, help="the file both sides started from")
        target.add_argument("--ours", required=True, help="our edited copy")
        target.add_argument("--theirs", required=True, help="their edited copy")
        target.add_argument(
            "--style", choices=STYLES, default="merge", help="conflict marker style"
        )
        target.add_argument(
            "--labels", default=None, help='two names for the markers, like "ours,theirs"'
        )

    merge = commands.add_parser("merge", help="write the merged text")
    inputs(merge)
    merge.add_argument("--out", default=None, help="write here instead of standard output")
    merge.add_argument("--json", action="store_true", help="print a verdict document")
    merge.add_argument("--quiet", action="store_true", help="no summary line on standard error")
    merge.set_defaults(handler=_command_merge)

    explain = commands.add_parser("explain", help="show the chunks before the merged text")
    inputs(explain)
    explain.set_defaults(handler=_command_explain)

    demo = commands.add_parser("demo", help="six merges with their claims checked")
    demo.set_defaults(handler=_command_demo)

    selftest = commands.add_parser("selftest", help="known answers, without pytest")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except UsageError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except MergeError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
