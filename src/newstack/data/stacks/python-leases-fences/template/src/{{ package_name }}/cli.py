"""Command line: run the stories, or the pause scenario as a table."""

from __future__ import annotations

import argparse
import sys

from .demo import render, timeline
from .lease import LeaseError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The command line does not describe a scenario we can run."""


def command_demo(args: argparse.Namespace) -> int:
    sys.stdout.write(render())
    return EXIT_OK


def command_model(args: argparse.Namespace) -> int:
    if args.ttl_ms < 1:
        raise UsageError("--ttl-ms must be at least 1")
    if args.pause_ms <= args.ttl_ms:
        raise UsageError(
            f"--pause-ms {args.pause_ms} must exceed --ttl-ms {args.ttl_ms}, "
            "otherwise the lease never expires and there is nothing to demonstrate"
        )
    rows, kept = timeline(args.ttl_ms, args.pause_ms)
    print("\n".join(rows))
    return EXIT_OK if kept else EXIT_BROKEN


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="leases with fencing tokens: the second half of the lock"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="six stories about expired leases")
    demo.set_defaults(func=command_demo)

    model = sub.add_parser("model", help="the pause scenario as a timeline")
    model.add_argument("--ttl-ms", type=int, default=1_000)
    model.add_argument("--pause-ms", type=int, default=1_500)
    model.set_defaults(func=command_model)

    selftest = sub.add_parser("selftest", help="check the invariants")
    selftest.set_defaults(func=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except (UsageError, LeaseError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
