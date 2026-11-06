"""Command line for the ignore matcher."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo as demo_module
from .matcher import Matcher, PathError, Verdict
from .pattern import PatternError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_IGNORED = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line asked for something that cannot be answered."""


def _load(path_text: str) -> tuple[Matcher, Path]:
    path = Path(path_text)
    matcher, _ = Matcher.from_file(path)
    return matcher, path


def _verdict_payload(verdict: Verdict) -> dict[str, object]:
    return {
        "path": verdict.path,
        "is_dir": verdict.is_dir,
        "ignored": verdict.ignored,
        "rule": None if verdict.rule is None else verdict.rule.text,
        "line": None if verdict.rule is None else verdict.rule.line,
        "reason": verdict.reason,
        "parent": verdict.parent,
    }


def _command_explain(args: argparse.Namespace) -> int:
    matcher, ignore_file = _load(args.ignore)
    verdict = matcher.decide(args.path, is_dir=args.directory)
    if args.json:
        print(json.dumps(_verdict_payload(verdict), indent=2, sort_keys=True))
    else:
        print(f"ignore     {ignore_file}")
        for line in verdict.lines():
            print(line)
    return EXIT_IGNORED if verdict.ignored else EXIT_OK


def _command_list(args: argparse.Namespace) -> int:
    matcher, ignore_file = _load(args.ignore)
    if args.json:
        payload = [
            {
                "line": rule.line,
                "text": rule.text,
                "negated": rule.negated,
                "dir_only": rule.dir_only,
                "anchored": rule.anchored,
            }
            for rule in matcher.rules
        ]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"ignore     {ignore_file}")
    print(f"rules      {len(matcher.rules)}")
    for rule in matcher.rules:
        flags = []
        if rule.negated:
            flags.append("negation")
        if rule.dir_only:
            flags.append("directory only")
        if rule.anchored:
            flags.append("anchored")
        suffix = f"  [{', '.join(flags)}]" if flags else ""
        print(f"{rule.line:>4}       {rule.text}{suffix}")
    return EXIT_OK


def _command_walk(args: argparse.Namespace) -> int:
    matcher, ignore_file = _load(args.ignore)
    root = Path(args.root)
    verdicts = matcher.walk(root)
    ignored = [verdict for verdict in verdicts if verdict.ignored]
    if args.json:
        payload = {
            "ignore": str(ignore_file),
            "root": str(root),
            "paths": len(verdicts),
            "ignored": len(ignored),
            "entries": [
                _verdict_payload(verdict) for verdict in verdicts if verdict.ignored or args.all
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    print(f"ignore     {ignore_file}")
    print(f"root       {root}")
    print(f"paths      {len(verdicts)}")
    print(f"ignored    {len(ignored)}")
    for verdict in verdicts:
        if not verdict.ignored and not args.all:
            continue
        mark = "ignored" if verdict.ignored else "tracked"
        detail = f"line {verdict.rule.line}" if verdict.rule is not None else "no rule"
        print(f"{mark:<8}   {verdict.path}  ({detail})")
    return EXIT_OK


def _command_demo(args: argparse.Namespace) -> int:
    del args
    return demo_module.run()


def _command_selftest(args: argparse.Namespace) -> int:
    del args
    from . import selftest

    return selftest.run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="decide what an ignore file means for a path",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    explain = sub.add_parser("explain", help="explain the verdict for one path")
    explain.add_argument("path", help="path relative to the tree root")
    explain.add_argument("--ignore", default=".gitignore", help="ignore file to read")
    explain.add_argument("--directory", action="store_true", help="treat the path as a directory")
    explain.add_argument("--json", action="store_true", help="print the verdict as JSON")
    explain.set_defaults(handler=_command_explain)

    listing = sub.add_parser("list", help="list the rules that were read")
    listing.add_argument("--ignore", default=".gitignore", help="ignore file to read")
    listing.add_argument("--json", action="store_true", help="print the rules as JSON")
    listing.set_defaults(handler=_command_list)

    walk = sub.add_parser("walk", help="decide every path under a directory")
    walk.add_argument("root", help="directory to walk")
    walk.add_argument("--ignore", default=".gitignore", help="ignore file to read")
    walk.add_argument("--all", action="store_true", help="print tracked paths too")
    walk.add_argument("--json", action="store_true", help="print the walk as JSON")
    walk.set_defaults(handler=_command_walk)

    demo = sub.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = sub.add_parser("selftest", help="check the rules against known answers")
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
    except (PatternError, PathError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
