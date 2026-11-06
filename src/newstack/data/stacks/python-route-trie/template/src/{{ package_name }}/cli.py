"""The command line: match, table, why, demo, selftest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import explain
from .demo import render_stories
from .pattern import PatternError
from .router import METHODS, NO_MATCH, Router, RouterError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NO_MATCH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command cannot be run as asked."""


def load_routes(path: str) -> Router:
    """Read ``METHOD /pattern`` lines, skipping blanks and comments."""
    source = Path(path)
    if not source.is_file():
        raise UsageError(f"no such route table: {path}")
    router = Router()
    for number, raw in enumerate(source.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise UsageError(
                f"{path}:{number} is {line!r}; a route line is 'METHOD /pattern' and nothing else"
            )
        method, pattern = parts
        try:
            router.add(method.upper(), pattern)
        except (PatternError, RouterError) as error:
            raise UsageError(f"{path}:{number}: {error}") from error
    if not router.routes:
        raise UsageError(f"{path} holds no routes, and a router with no routes matches nothing")
    return router


def _command_match(args: argparse.Namespace) -> int:
    router = load_routes(args.routes)
    resolution = router.match(args.method.upper(), args.path)
    if args.json:
        print(json.dumps(resolution.as_dict(), indent=2))
    else:
        for line in explain.resolution_lines(resolution):
            print(line)
        hint = explain.nearest_hint(router, args.path) if resolution.kind == NO_MATCH else ""
        if hint:
            print(f"hint       {hint}")
    return EXIT_OK if resolution.matched else EXIT_NO_MATCH


def _command_table(args: argparse.Namespace) -> int:
    router = load_routes(args.routes)
    if args.json:
        payload = [
            {
                "method": route.method,
                "pattern": route.pattern.text,
                "shape": route.pattern.shape(),
                "params": list(route.pattern.params),
            }
            for route in router.routes
        ]
        print(json.dumps(payload, indent=2))
        return EXIT_OK
    for line in explain.table_lines(router.routes):
        print(line)
    return EXIT_OK


def _command_why(args: argparse.Namespace) -> int:
    """Match every method in turn and report the first that answers."""
    router = load_routes(args.routes)
    resolution = router.match(args.method.upper(), args.path)
    if resolution.matched:
        print(f"{resolution.method} {args.path} is served by {resolution.route.text}")
        return EXIT_NO_MATCH
    tried: list[str] = []
    for method in METHODS:
        if method == args.method.upper():
            continue
        other = router.match(method, args.path)
        tried.append(f"{method:<7} {other.kind}")
        if other.matched:
            tried[-1] += f"  {other.route.text}"
            break
    print(f"verdict    {resolution.kind}")
    print(f"reason     {resolution.reason}")
    if resolution.allow:
        print(f"allow      {', '.join(resolution.allow)}")
    print("tried")
    for line in tried:
        print(f"  {line}")
    return EXIT_NO_MATCH


def _command_demo(_args: argparse.Namespace) -> int:
    for line in render_stories():
        print(line)
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Match request paths against a route table, and say why.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    match = sub.add_parser("match", help="match one method and path against a route table")
    match.add_argument("--routes", required=True)
    match.add_argument("--method", default="GET")
    match.add_argument("--path", required=True)
    match.add_argument("--json", action="store_true")
    match.set_defaults(handler=_command_match)

    table = sub.add_parser("table", help="print every registered route and its shape")
    table.add_argument("--routes", required=True)
    table.add_argument("--json", action="store_true")
    table.set_defaults(handler=_command_table)

    why = sub.add_parser("why", help="explain a miss by trying the other methods")
    why.add_argument("--routes", required=True)
    why.add_argument("--method", default="GET")
    why.add_argument("--path", required=True)
    why.set_defaults(handler=_command_why)

    demo = sub.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = sub.add_parser("selftest", help="check this build against its own claims")
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
    except (PatternError, RouterError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
