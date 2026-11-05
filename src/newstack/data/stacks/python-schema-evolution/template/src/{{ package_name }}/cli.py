"""diff two schemas, and prove the breaking findings with a real document."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import demo, schema
from .compare import compare

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BREAKING = 1
EXIT_UNUSABLE = 2

DEFAULT_OLD = Path("fixtures/v1.json")
DEFAULT_NEW = Path("fixtures/v2.json")


def add_schema_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--old", type=Path, default=DEFAULT_OLD, help="the schema in use")
    parser.add_argument("--new", type=Path, default=DEFAULT_NEW, help="the schema proposed")


def report_payload(report: Any) -> dict[str, Any]:
    return report.as_dict()


def command_diff(args: argparse.Namespace) -> int:
    report = compare(schema.load(args.old), schema.load(args.new))
    if args.json:
        print(json.dumps(report_payload(report), indent=2))
    else:
        for line in report.lines():
            print(line)
    return EXIT_BREAKING if report.fails(args.strict) else EXIT_OK


def command_demo(args: argparse.Namespace) -> int:
    proof, report, additive, undecidable = demo.run()
    for line in demo.render(proof, report, additive, undecidable):
        print(line)
    if not proof.ok:
        print(f"{PROGRAM}: {proof.unproven} breaking claim(s) have no document behind them")
        return EXIT_BREAKING
    return EXIT_OK


def command_selftest(args: argparse.Namespace) -> int:
    from .selftest import run

    return run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Classify a JSON Schema change, and prove the breaking claims.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)

    diff = commands.add_parser("diff", help="classify every change between two schemas")
    add_schema_arguments(diff)
    diff.add_argument("--strict", action="store_true", help="fail on risky findings too")
    diff.add_argument("--json", action="store_true", help="machine-readable report")
    diff.set_defaults(handler=command_diff)

    commands.add_parser("demo", help="prove each breaking finding with a document").set_defaults(
        handler=command_demo
    )
    commands.add_parser("selftest", help="check this tool against its own fixtures").set_defaults(
        handler=command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except schema.SchemaError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
