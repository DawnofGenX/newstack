"""Command line entry point for {{ title }}."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="{{ npm_name }}", description="{{ description }}")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    greet = sub.add_parser("greet", help="print a greeting")
    greet.add_argument("--name", default="world", help="who to greet")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "greet":
        print(f"Hello, {args.name}!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
