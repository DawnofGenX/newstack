"""Terminal front end: ask the limiter about a key, or replay a timeline of requests."""

from __future__ import annotations

import argparse
import json
import sys

from . import selftest as selftest_mod
from .clock import FakeClock
from .limiter import Limiter
from .model import MICROSECONDS, Config, Decision

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_DENIED = 1
EXIT_UNUSABLE = 2


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=100, help="requests per window (default 100)")
    parser.add_argument("--per", type=int, default=60, dest="per_seconds", help="window seconds")
    parser.add_argument("--capacity", type=int, default=None, help="burst size (default: limit)")


def decision_payload(decision: Decision) -> dict[str, object]:
    return {
        "allowed": decision.allowed,
        "key": decision.key,
        "cost": decision.cost,
        "remaining": decision.remaining,
        "retry_after_s": decision.retry_after_s,
        "reset_at_s": decision.reset_at_s,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A token bucket with no floats: ask about a key, or replay a timeline.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="ask the limiter about one key")
    check.add_argument("key", help="the key to spend from, e.g. a user id")
    check.add_argument("--cost", type=int, default=1, help="how many slots this request needs")
    check.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="spend this many times at the same instant, to walk into the limit",
    )
    check.add_argument("--json", action="store_true", help="print JSON")
    add_config_arguments(check)

    simulate = subparsers.add_parser("simulate", help="replay requests spaced `every` ms apart")
    simulate.add_argument("--requests", type=int, default=10)
    simulate.add_argument("--every", type=int, default=100, help="milliseconds between requests")
    simulate.add_argument("--cost", type=int, default=1)
    add_config_arguments(simulate)

    subparsers.add_parser("demo", help="burst, get denied, then recover")
    subparsers.add_parser("selftest", help="run the built-in checks")
    return parser


def command_check(args: argparse.Namespace) -> int:
    if args.repeat < 1:
        raise ValueError("--repeat must be at least 1")
    config = Config(limit=args.limit, per_seconds=args.per_seconds, capacity=args.capacity)
    # `--repeat` promises "at the same instant", so the clock must not move between the calls.
    limiter = Limiter(config, FakeClock())
    decisions = [limiter.check(args.key, args.cost) for _ in range(args.repeat)]
    if args.json:
        payload = [decision_payload(decision) for decision in decisions]
        print(json.dumps(payload[-1] if len(payload) == 1 else payload, indent=2))
    else:
        for decision in decisions:
            print(decision.line())
    return EXIT_OK if all(decision.allowed for decision in decisions) else EXIT_DENIED


def command_simulate(args: argparse.Namespace) -> int:
    if args.requests < 1:
        raise ValueError("--requests must be at least 1")
    if args.every < 0:
        raise ValueError("--every cannot be negative")
    config = Config(limit=args.limit, per_seconds=args.per_seconds, capacity=args.capacity)
    clock = FakeClock()
    limiter = Limiter(config, clock)
    allowed = 0
    for _ in range(args.requests):
        clock.advance(args.every * 1000)
        decision = limiter.check("client", args.cost)
        allowed += 1 if decision.allowed else 0
        print(f"t={clock.now_us() / MICROSECONDS:7.3f}s  {decision.line()}")
    burst, interval = config.burst, interval_s(config)
    print(f"\n{allowed} of {args.requests} allowed; burst {burst}, interval {interval:.3f}s")
    return EXIT_OK


def interval_s(config: Config) -> float:
    return config.per_seconds / config.limit


def command_demo(_args: argparse.Namespace) -> int:
    config = Config(limit=2, per_seconds=1, capacity=3)
    clock = FakeClock()
    limiter = Limiter(config, clock)
    print(f"burst {config.burst}, then one request every {interval_s(config):.3f}s\n")
    steps = (
        ("three at once", 0, 3),
        ("one too many at once", 0, 1),
        ("half an interval later", 250_000, 1),
        ("the next interval", 250_000, 1),
        ("a quiet second", 1_000_000, 1),
        ("a full bucket again", 2_000_000, 1),
    )
    for label, advance_us, count in steps:
        clock.advance(advance_us)
        for index in range(count):
            decision = limiter.check("client")
            at = clock.now_us() / MICROSECONDS
            text = label if count == 1 else f"{label} ({index + 1})"
            print(f"t={at:6.3f}s  {text:<24}  {decision.line()}")
    print(f"\nstats {limiter.stats()}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            return command_check(args)
        if args.command == "simulate":
            return command_simulate(args)
        if args.command == "demo":
            return command_demo(args)
        if args.command == "selftest":
            return selftest_mod.run()
    except (ValueError, TypeError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    return EXIT_UNUSABLE
