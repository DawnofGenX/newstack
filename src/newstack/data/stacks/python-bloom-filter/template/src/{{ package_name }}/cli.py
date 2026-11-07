"""The command line: one question per run, the array answers honestly.

Exit codes keep the promise visible to a shell: ``0`` means present
(or a clean audit), ``1`` means absent (or a broken audit), ``2``
means the arguments or the file cannot be used as given.
"""

from __future__ import annotations

import argparse
import json
import sys

from .audit import (
    CONFIGS,
    RECHECKS,
    estimate_items,
    shipped_audit,
)
from .bloom import ROWS, SEED, WIDTH, Bloom, BloomError
from .demo import stories
from .stream import LENGTH, Plan, StreamError, stream
from .universe import UniverseError, parse_key

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_MISS = 1
EXIT_UNUSABLE = 2


def _filter_from(seed: int, width: int, rows: int, seat: int) -> Bloom:
    bloom = Bloom(width=width, rows=rows, seed=seat)
    for key in stream(seed, LENGTH):
        bloom.add(key)
    return bloom


def _command_add(args: argparse.Namespace) -> int:
    bloom = Bloom(args.width, args.rows, args.seat)
    keys = [parse_key(text) for text in args.key]
    if not keys:
        raise UniverseError("add wants at least one --key")
    fresh = sum(bloom.add(key) for key in keys)
    if args.json:
        print(json.dumps({"added": keys, "bits_set": bloom.bits_set}, indent=2))
    else:
        listed = " ".join(str(key) for key in keys)
        print(f"added      {listed}")
        print(f"fresh bits {fresh} of {bloom.width} (width {bloom.width}, rows {bloom.rows})")
        print(f"audit      {len(bloom.audit())} breaks")
    return EXIT_OK


def _command_check(args: argparse.Namespace) -> int:
    key = parse_key(args.key)
    bloom = _filter_from(args.seed, args.width, args.rows, args.seat)
    present = bloom.might_contain(key)
    clear_row = bloom.first_clear_row(key)
    if args.json:
        print(
            json.dumps(
                {
                    "key": key,
                    "present": present,
                    "clear_row": clear_row,
                    "added": len(bloom.added),
                },
                indent=2,
            )
        )
    else:
        print(f"key        {key}")
        print(f"seed       {args.seed} (width {args.width}, rows {args.rows})")
        if present:
            print("answer     maybe: present (a collision can only lie this way)")
        else:
            print(f"answer     definite: absent (row {clear_row} was never raised)")
    return EXIT_OK if present else EXIT_MISS


def _command_report(args: argparse.Namespace) -> int:
    ledger = shipped_audit()
    breaks = ledger.breaks
    if args.json:
        payload = {
            "checks": ledger.checks,
            "verdicts": [
                {
                    "config": verdict.config,
                    "seed": verdict.seed,
                    "false_negatives": list(verdict.false_negatives),
                    "false_positives": list(verdict.false_positives),
                }
                for verdict in ledger.verdicts
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        widths = ", ".join(str(width) for _, width, _, _ in CONFIGS)
        print(f"configs    {len(CONFIGS)} (widths {widths})")
        print(f"streams    seeds 7 13 42 101 2026, {LENGTH} keys each")
        print(f"re-asks    {RECHECKS} booked, {ledger.checks} run")
        print(f"false neg  {sum(len(v.false_negatives) for v in ledger.verdicts)}")
        print(f"false pos  {sum(len(v.false_positives) for v in ledger.verdicts)}")
        crowded = _filter_from(7, 1024, 4, 11)
        print(f"estimate   {estimate_items(crowded):.3f} keys behind " f"{crowded.bits_set} bits")
        print(f"breaks     {len(breaks)}")
        for line in breaks[:5]:
            print(f"  - {line}")
    return EXIT_OK if not breaks else EXIT_MISS


def _command_seed(args: argparse.Namespace) -> int:
    plan = Plan.draw(args.value)
    first = Bloom(args.width, args.rows, args.seat)
    second = Bloom(args.width, args.rows, args.seat)
    for key in plan.keys:
        first.add(key)
    for key in stream(args.value, args.length):
        second.add(key)
    same = first.bits == second.bits and first.added == second.added
    if args.json:
        print(json.dumps({"seed": args.value, "keys": list(plan.keys)}, indent=2))
    else:
        head = " ".join(str(key) for key in plan.keys[:8])
        print(f"seed       {args.value}")
        print(f"first keys {head} ...")
        print(f"replay     {'identical' if same else 'DIVERGED'}")
    return EXIT_OK if same else EXIT_MISS


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_MISS


def _command_demo(_args: argparse.Namespace) -> int:
    told = stories()
    standing = sum(story.held for story in told)
    for story in told:
        mark = "holds" if story.held else "FAILS"
        print(f"  {mark:<6} {story.title}")
        print(f"         {story.detail}")
    print(f"stories    {standing} of {len(told)} hold")
    return EXIT_OK if standing == len(told) else EXIT_MISS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "A Bloom filter over [0, 256): add, check, report, seed, selftest, demo."
        ),
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="seat keys in a fresh array")
    add_parser.add_argument("--key", action="append", default=[], required=False)
    add_parser.add_argument("--width", type=int, default=WIDTH)
    add_parser.add_argument("--rows", type=int, default=ROWS)
    add_parser.add_argument("--seat", type=int, default=SEED)
    add_parser.add_argument("--json", action="store_true")
    add_parser.set_defaults(handler=_command_add)

    check_parser = subparsers.add_parser("check", help="ask one key of a seeded filter")
    check_parser.add_argument("key")
    check_parser.add_argument("--seed", type=int, default=7)
    check_parser.add_argument("--width", type=int, default=WIDTH)
    check_parser.add_argument("--rows", type=int, default=ROWS)
    check_parser.add_argument("--seat", type=int, default=SEED)
    check_parser.add_argument("--json", action="store_true")
    check_parser.set_defaults(handler=_command_check)

    report_parser = subparsers.add_parser("report", help="the shipped audit, counted")
    report_parser.add_argument("--json", action="store_true")
    report_parser.set_defaults(handler=_command_report)

    seed_parser = subparsers.add_parser("seed", help="the stream one seed draws")
    seed_parser.add_argument("value", type=int)
    seed_parser.add_argument("--length", type=int, default=LENGTH)
    seed_parser.add_argument("--width", type=int, default=WIDTH)
    seed_parser.add_argument("--rows", type=int, default=ROWS)
    seed_parser.add_argument("--seat", type=int, default=SEED)
    seed_parser.add_argument("--json", action="store_true")
    seed_parser.set_defaults(handler=_command_seed)

    selftest_parser = subparsers.add_parser("selftest", help="the invariants")
    selftest_parser.set_defaults(handler=_command_selftest)

    demo_parser = subparsers.add_parser("demo", help="the claims, computed live")
    demo_parser.set_defaults(handler=_command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (
        BloomError,
        StreamError,
        UniverseError,
    ) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
