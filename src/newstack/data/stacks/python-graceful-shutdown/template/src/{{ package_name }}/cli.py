"""Command line: serve the demo, or check the shutdown logic."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .service import EXIT_OK, serve

PROGRAM = "{{ npm_name }}"
DEFAULT_PORT = 5477


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A server that finishes in-flight work before it exits.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("serve", help="start the server and wait for a signal")
    run.add_argument("--port", type=int, default=DEFAULT_PORT)
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument(
        "--drain-timeout",
        type=float,
        default=10.0,
        help="seconds to wait for in-flight requests before exiting 1 (default: 10)",
    )
    commands.add_parser("selftest", help="check the lifecycle and a real signal")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "selftest":
        from .selftest import run_selftest

        return EXIT_OK if run_selftest() else 1
    try:
        return serve(port=args.port, host=args.host, drain_timeout=args.drain_timeout)
    except (OSError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 2
