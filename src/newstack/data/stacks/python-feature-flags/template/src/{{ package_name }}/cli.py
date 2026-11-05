"""Terminal front end: ask the flags about one user, or about a population."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import config
from . import selftest as selftest_mod
from .bucket import spread
from .evaluate import decide, explain
from .model import BPS, FlagSet, InputError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_ON = 0
EXIT_OFF = 1
EXIT_UNUSABLE = 2

DEFAULT_FLAGS = Path("fixtures/flags.toml")
PERCENT = BPS // 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Feature flags that can say why: stable buckets, integer percents, a reason.",
    )
    parser.add_argument("--flags", type=Path, default=DEFAULT_FLAGS, help="the flags file")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="does this user see this flag? (exit 1 when off)")
    check.add_argument("flag")
    check.add_argument("--user", required=True)
    check.add_argument("--json", action="store_true")

    tracer = subparsers.add_parser("explain", help="the decision and the rules behind it")
    tracer.add_argument("flag")
    tracer.add_argument("--user", required=True)

    listing = subparsers.add_parser("list", help="print every flag")
    listing.add_argument("--json", action="store_true")

    distribution = subparsers.add_parser("distribution", help="measured rollout over N users")
    distribution.add_argument("--users", type=int, default=10_000)
    distribution.add_argument("--json", action="store_true")

    subparsers.add_parser("selftest", help="run the built-in checks")
    return parser


def describe(flags: FlagSet, name: str, user: str) -> dict[str, Any]:
    decision = decide(flags, name, user)
    return decision.as_dict()


def command_check(flags: FlagSet, args: argparse.Namespace) -> int:
    decision = decide(flags, args.flag, args.user)
    if args.json:
        print(json.dumps(decision.as_dict(), indent=2))
    else:
        print(decision.line())
    return EXIT_ON if decision.on else EXIT_OFF


def command_explain(flags: FlagSet, args: argparse.Namespace) -> int:
    for line in explain(flags, args.flag, args.user):
        print(line)
    return EXIT_ON if decide(flags, args.flag, args.user).on else EXIT_OFF


def command_list(flags: FlagSet, args: argparse.Namespace) -> int:
    if args.json:
        payload = [
            {"name": flag.name, "enabled": flag.enabled, "rollout": flag.rollout, "salt": flag.salt}
            for flag in flags
        ]
        print(json.dumps(payload, indent=2))
        return EXIT_ON
    for flag in flags:
        print(flag.line())
    return EXIT_ON


def command_distribution(flags: FlagSet, args: argparse.Namespace) -> int:
    if args.users < 1:
        raise InputError(f"--users must be at least 1, got {args.users}")
    users = [f"user-{index:06d}" for index in range(args.users)]
    rows: list[dict[str, Any]] = []
    for flag in flags:
        counts = spread(flag.salt, users)
        inside_count = sum(count for percent, count in counts.items() if percent < flag.rollout)
        observed = 100.0 * inside_count / len(users)
        rows.append(
            {
                "flag": flag.name,
                "expected": flag.rollout,
                "observed": round(observed, 2),
                "deviation": round(observed - flag.rollout, 2),
            }
        )
    if args.json:
        print(json.dumps({"users": len(users), "flags": rows}, indent=2))
        return EXIT_ON
    print(f"{'flag':<24} {'wanted':>7} {'measured':>9} {'off by':>7}")
    for row in rows:
        print(
            f"{row['flag']:<24} {row['expected']:>6}% {row['observed']:>8}% "
            f"{row['deviation']:>+6}%"
        )
    worst = max(rows, key=lambda row: abs(row["deviation"]))
    print(f"\nworst deviation: {worst['flag']} at {worst['deviation']:+.2f} percentage points")
    return EXIT_ON


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "selftest":
        return selftest_mod.run()
    try:
        flags = config.load(args.flags)
        if args.command == "check":
            return command_check(flags, args)
        if args.command == "explain":
            return command_explain(flags, args)
        if args.command == "list":
            return command_list(flags, args)
        if args.command == "distribution":
            return command_distribution(flags, args)
    except (InputError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    return EXIT_UNUSABLE
