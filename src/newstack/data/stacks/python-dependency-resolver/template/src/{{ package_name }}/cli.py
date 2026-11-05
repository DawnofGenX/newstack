"""Command line: resolve, explain, check a lock, and prove the rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .index import IndexError_, load
from .lockfile import LockError, audit, read, write
from .ranges import RangeError, parse_range
from .resolver import Resolution, ResolveError, resolve

PROGRAM = "{{ npm_name }}"
EXIT_OK = 0
EXIT_UNSATISFIED = 1
EXIT_UNUSABLE = 2

DEFAULT_INDEX = Path("fixtures/index.json")


class UsageError(ValueError):
    """Raised for input the resolver should refuse before doing any work."""


def _parse_roots(values: list[str]) -> dict[str, str]:
    roots: dict[str, str] = {}
    for item in values:
        name, sep, constraint = item.partition("=")
        if not sep or not name.strip() or not constraint.strip():
            raise UsageError(f"--root {item!r} must look like name=RANGE, for example web=^2.0.0")
        if name.strip() in roots:
            raise UsageError(
                f"--root {name.strip()} is given twice; two roots cannot disagree and both be kept"
            )
        try:
            parse_range(constraint.strip())
        except RangeError as error:
            raise UsageError(f"--root {name.strip()}: {error}") from error
        roots[name.strip()] = constraint.strip()
    if not roots:
        raise UsageError("at least one --root is needed; nothing resolves an empty project")
    return roots


def _resolution_lines(resolution: Resolution) -> list[str]:
    lines = [
        choice.line()
        for choice in (resolution.choices[name] for name in sorted(resolution.choices))
    ]
    lines.append(
        f"resolved {resolution.count} package(s) after exploring "
        f"{resolution.explored} partial solution(s)"
    )
    return lines


def _cmd_resolve(args: argparse.Namespace) -> int:
    index = load(args.index)
    roots = _parse_roots(args.root)
    locked = read(args.lock).packages if args.lock else None
    resolution = resolve(index, roots, locked=locked)

    if args.write_lock:
        write(args.write_lock, resolution)

    if args.json:
        print(json.dumps(resolution.as_dict(), indent=2, sort_keys=True))
    else:
        print("\n".join(_resolution_lines(resolution)))
        if args.write_lock:
            print(f"wrote {args.write_lock}")
    return EXIT_OK


def _cmd_why(args: argparse.Namespace) -> int:
    index = load(args.index)
    roots = _parse_roots(args.root)
    resolution = resolve(index, roots)
    if args.package not in resolution.choices:
        print(
            f"{PROGRAM}: {args.package!r} is not in this resolution; "
            f"it chose {', '.join(sorted(resolution.choices))}",
            file=sys.stderr,
        )
        return EXIT_UNUSABLE
    print("\n".join(resolution.why(args.package)))
    return EXIT_OK


def _cmd_check(args: argparse.Namespace) -> int:
    index = load(args.index)
    lock = read(args.lock)
    roots = _parse_roots(args.root)
    drift = audit(index, lock, roots)
    if not drift:
        print(f"check: {args.lock} still resolves; {len(lock.packages)} package(s) agree")
        return EXIT_OK
    print("check: the lockfile no longer describes a resolvable tree")
    for entry in drift:
        print(entry.line())
    print(f"check: {len(drift)} drift(s)")
    return EXIT_UNSATISFIED


def _cmd_demo(_: argparse.Namespace) -> int:
    from .demo import main as demo_main

    return demo_main()


def _cmd_selftest(_: argparse.Namespace) -> int:
    from .selftest import main as selftest_main

    return selftest_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Resolve a dependency graph and explain every choice it makes.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def shared(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="package index JSON")
        sub.add_argument("--root", action="append", default=[], metavar="NAME=RANGE")

    resolve_parser = subparsers.add_parser("resolve", help="find one version per package")
    shared(resolve_parser)
    resolve_parser.add_argument("--lock", type=Path, help="lockfile to prefer")
    resolve_parser.add_argument("--write-lock", type=Path, metavar="PATH")
    resolve_parser.add_argument("--json", action="store_true")
    resolve_parser.set_defaults(handler=_cmd_resolve)

    why_parser = subparsers.add_parser("why", help="explain one chosen version")
    shared(why_parser)
    why_parser.add_argument("package")
    why_parser.set_defaults(handler=_cmd_why)

    check_parser = subparsers.add_parser("check", help="fail when the lockfile is out of date")
    shared(check_parser)
    check_parser.add_argument("--lock", type=Path, required=True)
    check_parser.set_defaults(handler=_cmd_check)

    demo_parser = subparsers.add_parser(
        "demo", help="the six stories, run against the fixture index"
    )
    demo_parser.set_defaults(handler=_cmd_demo)

    selftest_parser = subparsers.add_parser("selftest", help="prove the rules against a live index")
    selftest_parser.set_defaults(handler=_cmd_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ResolveError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNSATISFIED
    except (UsageError, IndexError_, LockError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
