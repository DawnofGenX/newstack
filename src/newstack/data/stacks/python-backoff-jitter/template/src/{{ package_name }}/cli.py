"""Command line entry point."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, demo
from .policies import POLICIES, PolicyError, by_name
from .simulate import Result, SimulationError, simulate

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2

ORDER = ("fixed", "exponential", "full-jitter", "equal-jitter", "decorrelated")


class UsageError(Exception):
    """The command line asked for something that cannot be answered."""


def result_json(result: Result) -> str:
    return json.dumps(
        {
            "policy": result.policy,
            "clients": result.clients,
            "seed": result.seed,
            "fail_ms": result.fail_ms,
            "bucket_ms": result.bucket_ms,
            "attempts": result.attempts,
            "retries": result.retries,
            "exhausted": result.exhausted,
            "done_ms": result.done_ms,
            "peak_retries": result.peak_retries,
            "peak_bucket_ms": result.peak_bucket_ms,
            "buckets_used": result.buckets_used,
            "max_delay_ms": result.max_delay_ms,
            "mean_delay_ms": result.mean_delay_ms,
        },
        indent=2,
        sort_keys=True,
    )


def command_simulate(args) -> int:
    policy = by_name(args.policy)
    result = simulate(
        policy,
        clients=args.clients,
        seed=args.seed,
        fail_ms=args.fail_ms,
        bucket_ms=args.bucket_ms,
        max_attempts=args.max_attempts,
    )
    if args.json:
        print(result_json(result))
    else:
        for line in result.lines():
            print(line)
    if args.max_peak is None:
        return EXIT_OK
    verdict = "ok" if result.peak_retries <= args.max_peak else "BREACH"
    if not args.json:
        print(f"gate         peak {result.peak_retries} <= {args.max_peak} {verdict}")
    return EXIT_OK if result.peak_retries <= args.max_peak else EXIT_BREACH


def command_compare(args) -> int:
    results = [
        simulate(
            POLICIES[name](),
            clients=args.clients,
            seed=args.seed,
            fail_ms=args.fail_ms,
            bucket_ms=args.bucket_ms,
        )
        for name in ORDER
    ]
    width = max(len("policy"), *(len(result.policy) for result in results))
    print(f"{'policy':<{width}}{'peak':>7}{'buckets':>9}{'retries':>9}{'settled':>10}")
    for result in results:
        print(
            f"{result.policy:<{width}}{result.peak_retries:>7}{result.buckets_used:>9}"
            f"{result.retries:>9}{result.done_ms:>10.0f}"
        )
    fixed, full = results[0], results[2]
    if fixed.peak_retries and full.peak_retries:
        factor = fixed.peak_retries / full.peak_retries
        print(f"pile-up      {fixed.peak_retries} simultaneous retries against "
              f"{full.peak_retries} ({factor:.1f}x lower)")
    print(f"cost         {full.done_ms - fixed.done_ms:.0f} ms of extra outage for the calmer wave")
    return EXIT_OK


def command_demo(args) -> int:
    sys.stdout.write(demo.render())
    return EXIT_OK if all(story.held for story in demo.stories()) else EXIT_BREACH


def command_selftest(args) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description="measure retry pile-ups")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("simulate", help="run one policy against one outage")
    run.add_argument("--policy", default="full-jitter",
                     help=f"one of: {', '.join(sorted(POLICIES))}")
    run.add_argument("--clients", type=int, default=200)
    run.add_argument("--seed", type=int, default=7)
    run.add_argument("--fail-ms", type=float, default=1_000.0)
    run.add_argument("--bucket-ms", type=float, default=10.0)
    run.add_argument("--max-attempts", type=int, default=20)
    run.add_argument("--max-peak", type=int, help="exit 1 when more retries share a bucket")
    run.add_argument("--json", action="store_true")
    run.set_defaults(handler=command_simulate)

    compare = subparsers.add_parser("compare", help="run every policy on the same outage")
    compare.add_argument("--clients", type=int, default=200)
    compare.add_argument("--seed", type=int, default=7)
    compare.add_argument("--fail-ms", type=float, default=1_000.0)
    compare.add_argument("--bucket-ms", type=float, default=10.0)
    compare.set_defaults(handler=command_compare)

    demo_parser = subparsers.add_parser("demo", help="run the six stories")
    demo_parser.set_defaults(handler=command_demo)

    selftest_parser = subparsers.add_parser("selftest", help="run the built-in checks")
    selftest_parser.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (UsageError, PolicyError, SimulationError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
