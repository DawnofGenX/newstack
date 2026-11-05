"""Terminal front end: append, read, and — the point of the stack — verify."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import demo
from . import selftest as selftest_mod
from .record import Event
from .store import Store, StoreError
from .verify import Checkpoint, checkpoint_of, verify

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"

EXIT_OK = 0
EXIT_BROKEN = 1
EXIT_UNUSABLE = 2

DEFAULT_DB = Path("audit.db")
DEFAULT_CHECKPOINT = Path("checkpoint.json")


def parse_details(pairs: list[str], blob: str | None) -> dict[str, Any]:
    """`--detail k=v` is always a string; `--detail-json` is how a value keeps its type."""
    detail: dict[str, Any] = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not separator or not key:
            raise ValueError(f"--detail wants key=value, got {pair!r}")
        if key in detail:
            raise ValueError(f"--detail {key} was given twice")
        detail[key] = value
    if blob is not None:
        try:
            extra = json.loads(blob)
        except json.JSONDecodeError as error:
            raise ValueError(f"--detail-json is not JSON: {error}") from error
        if not isinstance(extra, dict):
            raise ValueError("--detail-json must be a JSON object")
        clash = sorted(set(extra) & set(detail))
        if clash:
            raise ValueError(f"--detail and --detail-json both set {', '.join(clash)}")
        detail.update(extra)
    return detail


def event_payload(event: Event) -> dict[str, Any]:
    return {**event.body, "hash": event.hash}


def row_line(event: Event) -> str:
    return (
        f"{event.seq:>4}  {event.at}  {event.actor:<10} {event.action:<14} "
        f"{event.target:<18} {event.hash[:12]}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="An append-only log whose tampering is detectable, and detected.",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="the log (default audit.db)")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="add one event")
    append.add_argument("--actor", required=True)
    append.add_argument("--action", required=True)
    append.add_argument("--target", required=True)
    append.add_argument("--detail", action="append", default=[], metavar="KEY=VALUE")
    append.add_argument("--detail-json", default=None, metavar="JSON")
    append.add_argument("--at", default=None, help="an ISO-8601 UTC timestamp (default: now)")
    append.add_argument("--json", action="store_true")

    listing = subparsers.add_parser("list", help="print the events in order")
    listing.add_argument("--limit", type=int, default=None)
    listing.add_argument("--json", action="store_true")

    check = subparsers.add_parser("verify", help="recompute the chain")
    check.add_argument("--checkpoint", type=Path, default=None)
    check.add_argument("--json", action="store_true")

    point = subparsers.add_parser("checkpoint", help="remember the head somewhere else")
    point.add_argument("--out", type=Path, default=DEFAULT_CHECKPOINT)

    subparsers.add_parser("demo", help="edit, delete, and rebuild this log to show what notices")
    subparsers.add_parser("selftest", help="run the built-in checks")
    return parser


def command_append(store: Store, args: argparse.Namespace) -> int:
    detail = parse_details(args.detail, args.detail_json)
    event = store.append(
        actor=args.actor, action=args.action, target=args.target, detail=detail, at=args.at
    )
    if args.json:
        print(json.dumps(event_payload(event), indent=2))
    else:
        print(f"seq {event.seq}  hash {event.hash}")
        for line in event.lines()[1:]:
            print(f"  {line}")
    return EXIT_OK


def command_list(store: Store, args: argparse.Namespace) -> int:
    events = store.events(limit=args.limit)
    if args.json:
        print(json.dumps([event_payload(event) for event in events], indent=2))
        return EXIT_OK
    for event in events:
        print(row_line(event))
    print(f"\n{len(events)} event(s) listed; {store.count()} in the log")
    return EXIT_OK


def command_verify(store: Store, args: argparse.Namespace) -> int:
    checkpoint = Checkpoint.load(args.checkpoint) if args.checkpoint is not None else None
    report = verify(store, checkpoint)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        for line in report.lines():
            print(line)
        if checkpoint is not None:
            print(f"       against a checkpoint at seq {checkpoint.seq}")
    return EXIT_OK if report.ok else EXIT_BROKEN


def command_checkpoint(store: Store, args: argparse.Namespace) -> int:
    checkpoint = checkpoint_of(store)
    checkpoint.save(args.out)
    print(
        f"checkpoint  seq {checkpoint.seq}  count {checkpoint.count}  hash {checkpoint.hash[:16]}…"
    )
    print(f"wrote {args.out} — keep it somewhere the log's owner cannot write")
    return EXIT_OK


def command_demo(_args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory() as directory:
        steps = demo.run(Path(directory))
    for step in steps:
        for line in step.render():
            print(line)
        print()
    missed = [step for step in steps if not step.caught]
    print(f"demo: {len(steps)} scenarios, {len(missed)} missed")
    return EXIT_BROKEN if missed else EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "demo":
        return command_demo(args)
    if args.command == "selftest":
        return selftest_mod.run()
    try:
        with Store(args.db) as store:
            if args.command == "append":
                return command_append(store, args)
            if args.command == "list":
                return command_list(store, args)
            if args.command == "verify":
                return command_verify(store, args)
            if args.command == "checkpoint":
                return command_checkpoint(store, args)
    except (ValueError, TypeError, StoreError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    return EXIT_UNUSABLE
