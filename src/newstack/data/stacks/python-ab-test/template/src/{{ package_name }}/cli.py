"""The command line: a gate for a dashboard, not a replacement for one."""

from __future__ import annotations

import argparse
import json
import sys

from . import demo, selftest
from .sequential import obrien_fleming, simulate
from .srm import check
from .stats import Arm, StatsError, compare, detectable_lift, sample_per_arm

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line cannot describe an experiment."""


def _arm(text: str) -> Arm:
    try:
        return Arm.from_text(text)
    except StatsError as error:
        raise UsageError(str(error)) from error


def _command_compare(arguments: argparse.Namespace) -> int:
    control = _arm(arguments.control)
    treatment = _arm(arguments.treatment)
    result = compare(control, treatment, arguments.alpha)
    if arguments.json:
        print(
            json.dumps(
                {
                    "control": {"name": control.name, "rate": control.rate},
                    "treatment": {"name": treatment.name, "rate": treatment.rate},
                    "difference": result.difference,
                    "lift": result.lift,
                    "z": result.z,
                    "p_value": result.p_value,
                    "interval": [result.interval.low, result.interval.high],
                    "significant": result.significant(),
                    "direction": result.direction(),
                },
                indent=2,
            )
        )
    else:
        for line in result.lines():
            print(line)
        print("note         a p-value is only a fixed-horizon claim; see `peeking`")
    return EXIT_OK


def _command_srm(arguments: argparse.Namespace) -> int:
    result = check(_arm(arguments.control), _arm(arguments.treatment), alpha=arguments.alpha)
    if arguments.json:
        print(
            json.dumps(
                {
                    "ratio": result.ratio,
                    "expected": result.expected,
                    "chi_square": result.chi_square,
                    "p_value": result.p_value,
                    "mismatched": result.mismatched,
                },
                indent=2,
            )
        )
    else:
        for line in result.lines():
            print(line)
    return EXIT_REFUSED if result.mismatched else EXIT_OK


def _command_power(arguments: argparse.Namespace) -> int:
    needed = sample_per_arm(
        arguments.baseline, arguments.lift, alpha=arguments.alpha, power=arguments.power
    )
    print(f"baseline     {arguments.baseline:.2%}")
    treatment = arguments.baseline * (1 + arguments.lift)
    print(f"lift         {arguments.lift:+.1%} relative, so {treatment:.4%}")
    print(f"alpha        {arguments.alpha}   power {arguments.power}")
    print(f"per arm      {needed:,} visitors")
    print(f"both arms    {needed * 2:,} visitors")
    if arguments.visitors:
        reached = detectable_lift(
            arguments.baseline, arguments.visitors, alpha=arguments.alpha, power=arguments.power
        )
        print(f"at {arguments.visitors:,}   only a {reached:.2%} relative lift would be caught")
    return EXIT_OK


def _command_peeking(arguments: argparse.Namespace) -> int:
    world = simulate(
        baseline=arguments.baseline,
        visitors=arguments.visitors,
        looks=arguments.looks,
        trials=arguments.trials,
        seed=arguments.seed,
        alpha=arguments.alpha,
    )
    boundary = obrien_fleming(arguments.alpha, arguments.looks)
    if arguments.json:
        print(
            json.dumps(
                {
                    "trials": world.trials,
                    "one_look": world.rate(world.fixed_crossings),
                    "every_look": world.rate(world.peeking_crossings),
                    "boundary": world.rate(world.guarded_crossings),
                    "critical": list(boundary.critical),
                },
                indent=2,
            )
        )
        return EXIT_OK
    for line in world.lines():
        print(line)
    print(f"critical     first look |z| {boundary.at(1):.3f}, last look "
          f"|z| {boundary.at(arguments.looks):.3f}")
    guarded = world.rate(world.guarded_crossings)
    flat = world.rate(world.peeking_crossings)
    if guarded > 2.0 * arguments.alpha:
        print(f"verdict      the boundary did NOT hold: {guarded:.2%} against alpha "
              f"{arguments.alpha:.2%}")
        return EXIT_REFUSED
    print(f"verdict      the boundary held at {guarded:.2%}; the flat line spent {flat:.2%}")
    return EXIT_OK


def _command_demo(arguments: argparse.Namespace) -> int:
    del arguments
    return demo.main()


def _command_selftest(arguments: argparse.Namespace) -> int:
    del arguments
    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A/B test maths: intervals, peeking, sample ratio mismatch, sample size.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    compare_parser = commands.add_parser("compare", help="a fixed-horizon two-proportion test")
    compare_parser.add_argument("--control", required=True, help="name=conversions/visitors")
    compare_parser.add_argument("--treatment", required=True, help="name=conversions/visitors")
    compare_parser.add_argument("--alpha", type=float, default=0.05)
    compare_parser.add_argument("--json", action="store_true")
    compare_parser.set_defaults(handler=_command_compare)

    srm_parser = commands.add_parser("srm", help="sample ratio mismatch")
    srm_parser.add_argument("--control", required=True, help="name=conversions/visitors")
    srm_parser.add_argument("--treatment", required=True, help="name=conversions/visitors")
    srm_parser.add_argument("--alpha", type=float, default=0.001)
    srm_parser.add_argument("--json", action="store_true")
    srm_parser.set_defaults(handler=_command_srm)

    power_parser = commands.add_parser("power", help="how many visitors an effect needs")
    power_parser.add_argument("--baseline", type=float, required=True)
    power_parser.add_argument("--lift", type=float, required=True,
                              help="relative, so 0.05 is a 5%% lift")
    power_parser.add_argument("--alpha", type=float, default=0.05)
    power_parser.add_argument("--power", type=float, default=0.8)
    power_parser.add_argument("--visitors", type=int, default=0)
    power_parser.set_defaults(handler=_command_power)

    peek_parser = commands.add_parser("peeking", help="what looking every day costs")
    peek_parser.add_argument("--baseline", type=float, default=0.10)
    peek_parser.add_argument("--visitors", type=int, default=2000)
    peek_parser.add_argument("--looks", type=int, default=10)
    peek_parser.add_argument("--trials", type=int, default=1000)
    peek_parser.add_argument("--seed", type=int, default=7)
    peek_parser.add_argument("--alpha", type=float, default=0.05)
    peek_parser.add_argument("--json", action="store_true")
    peek_parser.set_defaults(handler=_command_peeking)

    demo_parser = commands.add_parser("demo", help="six stories, each of which must hold")
    demo_parser.set_defaults(handler=_command_demo)

    selftest_parser = commands.add_parser("selftest", help="the rules as in-process checks")
    selftest_parser.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return int(arguments.handler(arguments))
    except (UsageError, StatsError) as error:
        print(f"{PROGRAM}: error: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
