"""The command line: simulate one policy, compare all of them, or draw a curve."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, simulate
from .cache import POLICIES, CacheError
from .trace import TRACES, TraceError, build, describe

PROGRAM = "{{ npm_name }}"
VERSION = __version__

EXIT_OK = 0
EXIT_BREACH = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """A request the command line cannot answer."""


def _trace(arguments: argparse.Namespace) -> list[str]:
    return build(arguments.trace, arguments.accesses, seed=arguments.seed)


def _command_simulate(arguments: argparse.Namespace) -> int:
    data = _trace(arguments)
    result = simulate.run(arguments.policy, data, arguments.capacity)
    ceiling = simulate.ceiling(data, arguments.capacity)
    if arguments.json:
        print(json.dumps({**result.as_dict(), "ceiling": ceiling}, indent=2))
    else:
        print(f"trace        {arguments.trace} - {describe(arguments.trace)}")
        print(f"accesses     {result.accesses} over {len(set(data))} distinct key(s)")
        print(simulate.header())
        print(result.line())
        print(f"ceiling      {ceiling:.4f}")
        if arguments.min_hit_rate is not None:
            ok = result.hit_rate >= arguments.min_hit_rate
            print(
                f"gate         {result.hit_rate:.4f} >= {arguments.min_hit_rate:.4f} "
                f"{'ok' if ok else 'BREACH'}"
            )
            if not ok:
                return EXIT_BREACH
    if arguments.min_hit_rate is not None and result.hit_rate < arguments.min_hit_rate:
        return EXIT_BREACH
    return EXIT_OK


def _command_compare(arguments: argparse.Namespace) -> int:
    data = _trace(arguments)
    results = simulate.compare(data, arguments.capacity)
    ceiling = simulate.ceiling(data, arguments.capacity)
    best = simulate.winner(results)
    if arguments.json:
        print(
            json.dumps(
                {
                    "trace": arguments.trace,
                    "capacity": arguments.capacity,
                    "ceiling": ceiling,
                    "results": [result.as_dict() for result in results],
                },
                indent=2,
            )
        )
    else:
        print(f"trace        {arguments.trace} - {describe(arguments.trace)}")
        print(f"capacity     {arguments.capacity}, ceiling {ceiling:.4f}")
        print(simulate.header())
        for result in results:
            print(result.line())
        print(
            f"best         {best.policy} at {best.hit_rate:.4f}, "
            f"{ceiling - best.hit_rate:.4f} under the ceiling"
        )
    if arguments.min_hit_rate is not None and best.hit_rate < arguments.min_hit_rate:
        return EXIT_BREACH
    return EXIT_OK


def _command_curve(arguments: argparse.Namespace) -> int:
    data = _trace(arguments)
    results = simulate.capacity_curve(data, arguments.capacities, arguments.policy)
    if arguments.json:
        print(
            json.dumps(
                {
                    "trace": arguments.trace,
                    "policy": arguments.policy,
                    "points": [
                        {**result.as_dict(), "ceiling": simulate.ceiling(data, result.capacity)}
                        for result in results
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"trace        {arguments.trace} - {describe(arguments.trace)}")
        print(f"policy       {arguments.policy}")
        print("capacity   hit rate   ceiling")
        for result in results:
            ceiling = simulate.ceiling(data, result.capacity)
            print(f"{result.capacity:>8}   {result.hit_rate:>8.4f}   {ceiling:>7.4f}")
    return EXIT_OK


def _command_demo(arguments: argparse.Namespace) -> int:
    del arguments
    from . import demo

    return demo.main()


def _command_selftest(arguments: argparse.Namespace) -> int:
    del arguments
    from . import selftest

    return selftest.main()


def _capacities(text: str) -> list[int]:
    try:
        values = [int(part) for part in text.split(",") if part.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"capacities are whole numbers: {error}") from error
    if not values:
        raise argparse.ArgumentTypeError("give at least one capacity")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Compare cache replacement policies on a trace whose shape is printed.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    def add_trace(target: argparse.ArgumentParser) -> None:
        target.add_argument("--trace", choices=TRACES, default="zipf")
        target.add_argument("--accesses", type=int, default=20_000)
        target.add_argument("--seed", type=int, default=7)

    simulate_command = commands.add_parser("simulate", help="one policy on one trace")
    simulate_command.add_argument("--policy", choices=sorted(POLICIES), default="lru")
    simulate_command.add_argument("--capacity", type=int, default=100)
    simulate_command.add_argument("--min-hit-rate", type=float, default=None)
    simulate_command.add_argument("--json", action="store_true")
    add_trace(simulate_command)
    simulate_command.set_defaults(handler=_command_simulate)

    compare_command = commands.add_parser("compare", help="every policy on one trace")
    compare_command.add_argument("--capacity", type=int, default=100)
    compare_command.add_argument("--min-hit-rate", type=float, default=None)
    compare_command.add_argument("--json", action="store_true")
    add_trace(compare_command)
    compare_command.set_defaults(handler=_command_compare)

    curve_command = commands.add_parser("curve", help="one policy at several capacities")
    curve_command.add_argument("--policy", choices=sorted(POLICIES), default="lru")
    curve_command.add_argument(
        "--capacities", type=_capacities, default=[10, 25, 50, 100, 200, 400]
    )
    curve_command.add_argument("--json", action="store_true")
    add_trace(curve_command)
    curve_command.set_defaults(handler=_command_curve)

    demo_command = commands.add_parser("demo", help="six stories, each of which must hold")
    demo_command.set_defaults(handler=_command_demo)

    selftest_command = commands.add_parser("selftest", help="the rules as in-process checks")
    selftest_command.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except (UsageError, CacheError, TraceError, simulate.SimulationError, ValueError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
