"""The command line: one question per run."""

from __future__ import annotations

import argparse
import json
import sys

from .demo import stories
from .solve import KnapsackError, audit, solve, witness

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKE = 1
EXIT_UNUSABLE = 2


def _parse_ints(text: str) -> list:
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            raise KnapsackError(f"no integer label: {part!r}") from None
    return out


def _run(fn, args) -> int:
    try:
        weights = _parse_ints(args.weights)
        values = _parse_ints(args.values)
        capacity = int(args.capacity)
    except (KnapsackError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        got = fn(weights, values, capacity)
    except KnapsackError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(weights, values, capacity)
    if breaks:
        print(f"{PROGRAM}: {breaks[0]}", file=sys.stderr)
        return EXIT_BROKE
    if args.json:
        print(json.dumps(got))
    else:
        print(f"value: {got}" if fn is solve else f"witness: {got}")
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog=PROGRAM)
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command")

    p_solve = sub.add_parser("solve", help="maximum value")
    p_solve.add_argument("weights")
    p_solve.add_argument("values")
    p_solve.add_argument("capacity")
    p_solve.add_argument("--json", action="store_true")
    p_solve.set_defaults(func=lambda a: _run(solve, a))

    p_wit = sub.add_parser("witness", help="chosen items")
    p_wit.add_argument("weights")
    p_wit.add_argument("values")
    p_wit.add_argument("capacity")
    p_wit.add_argument("--json", action="store_true")
    p_wit.set_defaults(func=lambda a: _run(witness, a))

    p_audit = sub.add_parser("audit", help="audit a claim")
    p_audit.add_argument("weights")
    p_audit.add_argument("values")
    p_audit.add_argument("capacity")
    p_audit.add_argument("--json", action="store_true")
    p_audit.set_defaults(func=lambda a: _audit(a))

    sub.add_parser("demo", help="run the stories").set_defaults(func=_demo)
    sub.add_parser("selftest", help="run the promises").set_defaults(func=_selftest)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_OK
    return args.func(args)


def _audit(args) -> int:
    try:
        weights = _parse_ints(args.weights)
        values = _parse_ints(args.values)
        capacity = int(args.capacity)
    except (KnapsackError, ValueError) as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    breaks = audit(weights, values, capacity)
    if args.json:
        print(json.dumps(breaks))
    else:
        print("audit: " + ("clean" if not breaks else breaks[0]))
    return EXIT_OK if not breaks else EXIT_BROKE


def _demo(args) -> int:
    told = stories()
    for story in told:
        print(f"{story.title}: {'ok' if story.held else 'FAIL'}")
    held = sum(1 for s in told if s.held)
    print(f"{held} of {len(told)} hold")
    return EXIT_OK


def _selftest(args) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_BROKE


if __name__ == "__main__":
    raise SystemExit(main())
