"""The command line: issue identifiers, read them back, audit a stream."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import demo as demo_module
from .audit import audit
from .generator import ClockError, ManualClock, SnowflakeGenerator
from .layout import (
    EPOCH_MS,
    IDS_PER_MS,
    MAX_SEQUENCE,
    MAX_WORKER,
    WORKERS,
    LayoutError,
    capacity_lines,
    decode,
)

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments cannot produce an answer."""


def _count(text: str) -> int:
    try:
        value = int(text)
    except ValueError as error:
        raise UsageError(f"{text!r} is not a whole number") from error
    if value < 0:
        raise UsageError("a count is not negative")
    return value


def _identifier(text: str) -> int:
    try:
        return int(text)
    except ValueError as error:
        raise UsageError(f"{text!r} is not an identifier") from error


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))


def _command_generate(arguments) -> int:
    count = _count(arguments.count)
    clock = ManualClock(arguments.epoch + arguments.start_ms)
    generator = SnowflakeGenerator(
        arguments.worker,
        clock=clock,
        epoch_ms=arguments.epoch,
        on_rollback=arguments.on_rollback,
    )
    values: list[int] = []
    while len(values) < count:
        values.append(generator.next_id())
        if arguments.spread:
            clock.advance(1)
    payload = {
        "worker": arguments.worker,
        "count": count,
        "ids": values,
        "stats": generator.stats(),
        "decoded": [decode(value).as_dict(arguments.epoch) for value in values[:5]],
    }
    _emit(payload, arguments.json)
    if arguments.json:
        return EXIT_OK
    for value in values:
        print(
            f"{value}  {decode(value).at(arguments.epoch).isoformat()}  "
            f"worker {decode(value).worker}  sequence {decode(value).sequence}"
        )
    print(f"issued       {len(values)} identifier(s) from worker {arguments.worker}")
    print(f"waits        {generator.waits}")
    return EXIT_OK


def _command_decode(arguments) -> int:
    decoded = decode(_identifier(arguments.id))
    payload = decoded.as_dict(arguments.epoch)
    _emit(payload, arguments.json)
    if not arguments.json:
        print(decoded.text(arguments.epoch))
    return EXIT_OK


def _command_audit(arguments) -> int:
    try:
        text = Path(arguments.input).read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise UsageError(f"no such file: {arguments.input}") from error
    values = [_identifier(line.strip()) for line in text.splitlines() if line.strip()]
    if not values:
        raise UsageError("this file holds no identifiers, so there is nothing to audit")
    report = audit(values, epoch_ms=arguments.epoch)
    payload = {
        "count": report.count,
        "distinct": report.distinct,
        "duplicates": report.duplicates,
        "monotone": report.monotone,
        "out_of_order": report.out_of_order,
        "workers": list(report.workers),
        "span_ms": report.span_ms,
        "per_second": report.per_second,
    }
    _emit(payload, arguments.json)
    if not arguments.json:
        for line in report.lines():
            print(line)
        print(f"verdict      {'sound' if report.held() else 'BROKEN'}")
    return EXIT_OK if report.held() else EXIT_INVALID


def _command_capacity(arguments) -> int:
    lines = capacity_lines(arguments.epoch)
    payload = {
        "workers": WORKERS,
        "ids_per_ms": IDS_PER_MS,
        "max_sequence": MAX_SEQUENCE,
        "max_worker": MAX_WORKER,
        "epoch_ms": arguments.epoch,
        "lines": lines,
    }
    _emit(payload, arguments.json)
    if not arguments.json:
        for line in lines:
            print(line)
    return EXIT_OK


def _command_demo(_arguments) -> int:
    return demo_module.main()


def _command_selftest(_arguments) -> int:
    from . import selftest

    return selftest.main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Snowflake identifiers with an honest clock and a finite sequence.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate", help="issue identifiers from one worker")
    generate.add_argument("--count", default="5")
    generate.add_argument("--worker", type=int, default=0)
    generate.add_argument("--start-ms", type=int, default=0)
    generate.add_argument("--epoch", type=int, default=EPOCH_MS)
    generate.add_argument("--on-rollback", choices=("refuse", "hold"), default="refuse")
    generate.add_argument("--spread", action="store_true", help="advance the clock per identifier")
    generate.add_argument("--json", action="store_true")
    generate.set_defaults(handler=_command_generate)

    decode_command = subparsers.add_parser("decode", help="read one identifier back")
    decode_command.add_argument("id")
    decode_command.add_argument("--epoch", type=int, default=EPOCH_MS)
    decode_command.add_argument("--json", action="store_true")
    decode_command.set_defaults(handler=_command_decode)

    audit_command = subparsers.add_parser("audit", help="check a stream of identifiers")
    audit_command.add_argument("--input", required=True)
    audit_command.add_argument("--epoch", type=int, default=EPOCH_MS)
    audit_command.add_argument("--json", action="store_true")
    audit_command.set_defaults(handler=_command_audit)

    capacity = subparsers.add_parser("capacity", help="what the 64 bits buy")
    capacity.add_argument("--epoch", type=int, default=EPOCH_MS)
    capacity.add_argument("--json", action="store_true")
    capacity.set_defaults(handler=_command_capacity)

    demo = subparsers.add_parser("demo", help="run the six stories")
    demo.set_defaults(handler=_command_demo)

    selftest = subparsers.add_parser("selftest", help="run the in-process checks")
    selftest.set_defaults(handler=_command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    handler = getattr(arguments, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_UNUSABLE
    try:
        return int(handler(arguments))
    except UsageError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except (LayoutError, ClockError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
