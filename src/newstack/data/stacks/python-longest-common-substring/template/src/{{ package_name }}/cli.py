"""The command line: one question per run."""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import LongestCommonSubstringError, audit, solve, witness

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _run_solve(args) -> int:
    try:
        got = solve(args.a, args.b)
    except LongestCommonSubstringError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        breaks = audit(args.a, args.b)
    except LongestCommonSubstringError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(got))
    else:
        print(f"answer: {got}")
    return EXIT_OK


def _run_witness(args) -> int:
    try:
        got = witness(args.a, args.b)
    except LongestCommonSubstringError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        breaks = audit(args.a, args.b)
    except LongestCommonSubstringError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(got))
    else:
        print(f"witness: {got}")
    return EXIT_OK


def _run_audit(args) -> int:
    try:
        breaks = audit(args.a, args.b)
    except LongestCommonSubstringError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    if breaks:
        for b in breaks:
            print(b)
        return EXIT_BROKE
    print("audit: clean")
    return EXIT_OK


def _run_demo(args) -> int:
    told = stories()
    for story in told:
        mark = "ok" if story.held else "FAIL"
        print(f"{mark} {story.title}: {story.detail}")
    failed = [s for s in told if not s.held]
    return EXIT_OK if not failed else EXIT_BROKE


def _run_selftest(args) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog=PROGRAM)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="longest common substring length")
    p_solve.add_argument("a")
    p_solve.add_argument("b")
    p_solve.add_argument("--json", action="store_true")
    p_solve.set_defaults(func=_run_solve)

    p_wit = sub.add_parser("witness", help="one longest common substring")
    p_wit.add_argument("a")
    p_wit.add_argument("b")
    p_wit.add_argument("--json", action="store_true")
    p_wit.set_defaults(func=_run_witness)

    p_audit = sub.add_parser("audit", help="check internal consistency")
    p_audit.add_argument("a")
    p_audit.add_argument("b")
    p_audit.set_defaults(func=_run_audit)

    p_demo = sub.add_parser("demo", help="run the built-in stories")
    p_demo.set_defaults(func=_run_demo)

    p_self = sub.add_parser("selftest", help="run the promise suite")
    p_self.set_defaults(func=_run_selftest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
