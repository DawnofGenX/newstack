"""The command line: one question per run.

make builds a deque, append/appendleft push, pop/popleft pull,
peek/peekleft read, rotate shifts, tolist lists, demo tells the
stories, selftest runs the promises. Every answer is computed
against the real modules.
"""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import (
    DequeError,
    append,
    append_left,
    make_deque,
    peek,
    peek_left,
    pop,
    pop_left,
    rotate,
    to_list,
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
            raise DequeError(f"no integer label: {t!r}") from None
    return out


def _make(args) -> int:
    try:
        values = _values_of(args.values) if args.values else []
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        d = make_deque(values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if args.json:
        print(json.dumps(to_list(d)))
        return EXIT_OK
    print(f"size       {len(d)}")
    print(f"deque      {to_list(d)}")
    return EXIT_OK


def _simple(args, fn, verb) -> int:
    try:
        d = make_deque(_values_of(args.values))
    except (DequeError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        result = fn(d)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if verb == "pop":
        print(f"popped     {result}")
        print(f"deque      {to_list(d)}")
    elif verb == "peek":
        print(f"peek       {result}")
    elif verb == "rotate":
        steps = int(args.steps)
        rotate(d, steps)
        print(f"deque      {to_list(d)}")
    else:
        print(f"deque      {to_list(d)}")
    return EXIT_OK


def _command_demo(_args) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_BROKE


def _command_selftest(_args) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description="a double-ended queue of integers.")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("make", help="values in, deque out")
    p.add_argument("values", nargs="*")
    p.add_argument("--json", action="store_true")
    p.set_defaults(handler=_make)

    p = sub.add_parser("append", help="append right")
    p.add_argument("values", nargs="+")
    p.set_defaults(handler=lambda a: _append_cmd(a, right=True))
    p = sub.add_parser("appendleft", help="append left")
    p.add_argument("values", nargs="+")
    p.set_defaults(handler=lambda a: _append_cmd(a, right=False))

    p = sub.add_parser("pop", help="pop right")
    p.add_argument("values", nargs="*")
    p.set_defaults(handler=lambda a: _pop_cmd(a, right=True))
    p = sub.add_parser("popleft", help="pop left")
    p.add_argument("values", nargs="*")
    p.set_defaults(handler=lambda a: _pop_cmd(a, right=False))

    p = sub.add_parser("peek", help="peek right")
    p.add_argument("values", nargs="+")
    p.set_defaults(handler=lambda a: _peek_cmd(a, right=True))
    p = sub.add_parser("peekleft", help="peek left")
    p.add_argument("values", nargs="+")
    p.set_defaults(handler=lambda a: _peek_cmd(a, right=False))

    p = sub.add_parser("rotate", help="rotate by steps")
    p.add_argument("steps")
    p.add_argument("values", nargs="*")
    p.set_defaults(handler=_rotate_cmd)

    p = sub.add_parser("tolist", help="list contents")
    p.add_argument("values", nargs="*")
    p.set_defaults(handler=_tolist_cmd)

    sub.add_parser("demo", help="stories").set_defaults(handler=_command_demo)
    sub.add_parser("selftest", help="promises").set_defaults(handler=_command_selftest)
    return parser


def _append_cmd(args, right=True) -> int:
    try:
        values = _values_of(args.values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    # last token is value, rest is deque
    if len(values) < 1:
        print(f"{PROGRAM}: need a value", file=sys.stderr)
        return EXIT_UNUSABLE
    value = values[-1]
    base = values[:-1]
    try:
        d = make_deque(base)
        if right:
            append(d, value)
        else:
            append_left(d, value)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"deque      {to_list(d)}")
    return EXIT_OK


def _pop_cmd(args, right=True) -> int:
    try:
        values = _values_of(args.values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        d = make_deque(values)
        result = pop(d) if right else pop_left(d)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"popped     {result}")
    print(f"deque      {to_list(d)}")
    return EXIT_OK


def _peek_cmd(args, right=True) -> int:
    try:
        values = _values_of(args.values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        d = make_deque(values)
        result = peek(d) if right else peek_left(d)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"peek       {result}")
    return EXIT_OK


def _rotate_cmd(args) -> int:
    try:
        steps = int(args.steps)
    except ValueError:
        print(f"{PROGRAM}: no integer label: {args.steps!r}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        values = _values_of(args.values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        d = make_deque(values)
        rotate(d, steps)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"deque      {to_list(d)}")
    return EXIT_OK


def _tolist_cmd(args) -> int:
    try:
        values = _values_of(args.values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        d = make_deque(values)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    print(f"deque      {to_list(d)}")
    return EXIT_OK


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 0
    try:
        return args.handler(args)
    except DequeError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
