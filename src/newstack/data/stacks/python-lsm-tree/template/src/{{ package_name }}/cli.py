"""The command line: one question per run, and a report that names the levels."""

from __future__ import annotations

import argparse
import json
import sys

from .demo import render_stories
from .levels import LevelError
from .ops import OpsError, load_ops, replay_dict
from .table import LSMTable, TableError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_NONE = 1
EXIT_UNUSABLE = 2


class UsageError(ValueError):
    """The arguments do not describe a question that can be asked."""


def _table(args: argparse.Namespace) -> LSMTable:
    return LSMTable(args.dir, memtable_limit=args.limit)


def _open_workload(args: argparse.Namespace) -> LSMTable:
    table = LSMTable(args.dir, memtable_limit=args.limit)
    for op, key, value in load_ops(args.ops):
        if op == "put":
            assert value is not None
            table.put(key, value)
        elif op == "del":
            table.delete(key)
    table.flush()
    return table


def _command_put(args: argparse.Namespace) -> int:
    table = _table(args)
    table.put(args.key, args.value)
    seq = table.flush()
    print(f"key        {args.key}")
    print(f"value      {args.value}")
    print(f"flushed    {seq}")
    return EXIT_OK


def _command_get(args: argparse.Namespace) -> int:
    table = _table(args)
    found = table.get(args.key)
    if args.json:
        print(json.dumps({"key": args.key, "value": found}, indent=2))
    else:
        print(f"key        {args.key}")
        print(f"value      {found}")
    return EXIT_OK if found is not None else EXIT_NONE


def _command_delete(args: argparse.Namespace) -> int:
    table = _table(args)
    table.delete(args.key)
    seq = table.flush()
    print(f"key        {args.key}")
    print("tombstone  written")
    print(f"flushed    {seq}")
    return EXIT_OK


def _command_load(args: argparse.Namespace) -> int:
    table = _open_workload(args)
    if args.json:
        print(json.dumps({"keys": table.keys(), "flushes": table.flushes}, indent=2))
    else:
        print(f"flushes    {table.flushes}, levels {table.level_count()}")
        for key, value in table.items():
            print(f"  {key}\t{value}")
    return EXIT_OK if table.items() else EXIT_NONE


def _command_flush(args: argparse.Namespace) -> int:
    table = _table(args)
    seq = table.flush()
    if args.json:
        print(json.dumps({"flushed": seq, "levels": table.level_count()}, indent=2))
    else:
        print(f"flushed    {seq}")
        print(f"levels     {table.level_count()}")
    return EXIT_OK if seq is not None else EXIT_NONE


def _command_compact(args: argparse.Namespace) -> int:
    table = _table(args)
    report = table.compact()
    if args.json:
        print(
            json.dumps(
                {"kept": report.kept, "dropped": report.dropped, "tables": report.tables},
                indent=2,
            )
        )
    else:
        print(f"tables     {report.tables} merged into 1")
        print(f"kept       {report.kept}, dropped {report.dropped} tombstone(s)")
    return EXIT_OK if report.kept or report.dropped else EXIT_NONE


def _command_workload(args: argparse.Namespace) -> int:
    from .ops import workload

    stream = workload(args.ops, seed=args.seed, low=args.low, high=args.high)
    dict_answers = replay_dict(stream)
    table = LSMTable(args.dir, memtable_limit=args.limit)
    for op, key, value in stream:
        if op == "put":
            assert value is not None
            table.put(key, value)
        elif op == "del":
            table.delete(key)
    answers = dict(table.items())
    agreed = answers == dict_answers
    if args.json:
        print(
            json.dumps(
                {"seed": args.seed, "flushes": table.flushes, "agreed": agreed},
                indent=2,
            )
        )
    else:
        print(f"seed       {args.seed}, ops {args.ops}, limit {args.limit}")
        print(f"flushes    {table.flushes}, levels {table.level_count()}")
        print(f"agreed     {agreed} against the dict")
    return EXIT_OK if agreed else EXIT_NONE


def _command_demo(_args: argparse.Namespace) -> int:
    text, held = render_stories()
    print(text)
    return EXIT_OK if held else EXIT_NONE


def _command_selftest(_args: argparse.Namespace) -> int:
    from .selftest import run

    report = run()
    print(report.render())
    return EXIT_OK if report.failed == 0 else EXIT_NONE


def _directory_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dir", required=True, help="the table directory on disk")
    parser.add_argument("--limit", type=int, default=8, help="memtable limit, 1 or more")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "A log-structured merge table: writes in a memtable, levels on disk, "
            "reads newest-first, compaction drops tombstones."
        ),
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    put_parser = subparsers.add_parser("put", help="write one key and value")
    _directory_args(put_parser)
    put_parser.add_argument("--key", type=int, required=True)
    put_parser.add_argument("--value", required=True)
    put_parser.set_defaults(handler=_command_put)

    get_parser = subparsers.add_parser("get", help="one key, newest level first")
    _directory_args(get_parser)
    get_parser.add_argument("--key", type=int, required=True)
    get_parser.add_argument("--json", action="store_true")
    get_parser.set_defaults(handler=_command_get)

    delete_parser = subparsers.add_parser("delete", help="bury a key under a tombstone")
    _directory_args(delete_parser)
    delete_parser.add_argument("--key", type=int, required=True)
    delete_parser.set_defaults(handler=_command_delete)

    load_parser = subparsers.add_parser("load", help="replay an op file into the table")
    _directory_args(load_parser)
    load_parser.add_argument("--ops", required=True, help="one op per line")
    load_parser.add_argument("--json", action="store_true")
    load_parser.set_defaults(handler=_command_load)

    flush_parser = subparsers.add_parser("flush", help="freeze the memtable to a level")
    _directory_args(flush_parser)
    flush_parser.add_argument("--json", action="store_true")
    flush_parser.set_defaults(handler=_command_flush)

    compact_parser = subparsers.add_parser(
        "compact", help="merge every level, drop every tombstone"
    )
    _directory_args(compact_parser)
    compact_parser.add_argument("--json", action="store_true")
    compact_parser.set_defaults(handler=_command_compact)

    workload_parser = subparsers.add_parser(
        "workload", help="a seeded mix against a dict, in a fresh table"
    )
    _directory_args(workload_parser)
    workload_parser.add_argument("--ops", type=int, default=240)
    workload_parser.add_argument("--seed", type=int, default=7)
    workload_parser.add_argument("--low", type=int, default=-60)
    workload_parser.add_argument("--high", type=int, default=60)
    workload_parser.add_argument("--json", action="store_true")
    workload_parser.set_defaults(handler=_command_workload)

    subparsers.add_parser("demo", help="the stories, computed live").set_defaults(
        handler=_command_demo
    )
    subparsers.add_parser("selftest", help="run the invariants").set_defaults(
        handler=_command_selftest
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_request:  # --version and --help end the run here
        return int(exit_request.code or 0)
    try:
        return int(args.handler(args))
    except (LevelError, OpsError, TableError, UsageError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except OSError as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
