"""The command line: one question per run, the real modules consulted."""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import (
    MonotonicError,
    audit,
    next_greater,
    next_smaller,
    previous_greater,
)

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _values_of(tokens: list) -> list:
    out = []
    for t in tokens:
        try:
            out.append(int(t))
        except ValueError:
            raise MonotonicError(f"no integer label: {t!r}") from None
    return out


def _command_greater(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = next_greater(values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"values     {len(values)}")
    print(f"greater    {got}")
    return EXIT_OK


def _command_smaller(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = next_smaller(values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"values     {len(values)}")
    print(f"smaller    {got}")
    return EXIT_OK


def _command_previous(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = previous_greater(values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"values     {len(values)}")
    print(f"previous   {got}")
    return EXIT_OK


def _command_audit(args: argparse.Namespace) -> int:
    try:
        values = _values_of(args.values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = audit(values)
    except MonotonicError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(got))
        return EXIT_OK
    print(f"length     {got['length']}")
    print(f"greater    {got['next_greater_count']}")
    print(f"smaller    {got['next_smaller_count']}")
    print(f"previous   {got['previous_greater_count']}")
    return EXIT_OK


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
    held = sum(1 for story in told if story.held)
    print(f"demo: {held} of {len(told)} hold")
    return EXIT_OK if all(story.held for story in told) else EXIT_BROKE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROGRAM)
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, fn, help_text in (
        ("greater", _command_greater, "next greater elements"),
        ("smaller", _command_smaller, "next smaller elements"),
        ("previous", _command_previous, "previous greater elements"),
        ("audit", _command_audit, "audit a list"),
        ("demo", _command_demo, "run demo stories"),
        ("selftest", _command_selftest, "run selftest"),
    ):
        p = sub.add_parser(name, help=help_text)
        if name not in ("demo", "selftest"):
            p.add_argument("values", nargs="+")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=fn)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
