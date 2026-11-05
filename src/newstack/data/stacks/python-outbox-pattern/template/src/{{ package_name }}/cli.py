"""Command line around the store, the relay and the demo."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import demo as demo_mod
from .model import Event, InputError
from .relay import SinkError, publish
from .store import Store, StoreError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_BACKLOG = 1
EXIT_UNUSABLE = 2
DEFAULT_DB = Path("outbox.db")


def print_event(event: Event) -> None:
    payload = json.dumps(event.envelope(), sort_keys=True)
    print(f"publish {event.event_id} {event.aggregate} seq {event.seq} {payload}")


def command_place(store: Store, args: argparse.Namespace) -> int:
    order, event = store.place_order(args.amount)
    print(f"placed  order {order.ident} for {order.amount}")
    print(f"event   {event.event_id} seq {event.seq} (pending: {store.pending_count()})")
    return EXIT_OK


def command_pay(store: Store, args: argparse.Namespace) -> int:
    event = store.pay_order(args.order)
    print(f"paid    order {args.order}")
    print(f"event   {event.event_id} seq {event.seq} (pending: {store.pending_count()})")
    return EXIT_OK


def command_show(store: Store, args: argparse.Namespace) -> int:
    orders = store.orders()
    events = store.events(pending_only=args.pending)
    for order in orders:
        print(f"order {order.ident:>4}  {order.amount:>8}  {order.status}")
    for event in events:
        print(event.line())
    print(f"{len(orders)} order(s), {len(events)} event(s) shown, {store.pending_count()} pending")
    return EXIT_OK


def command_relay(store: Store, args: argparse.Namespace) -> int:
    report = publish(store, print_event, limit=args.limit, crash_after=args.crash_after)
    print(f"relay   {report.line()}")
    if report.crashed_at is not None:
        print("the process died after the sink accepted it and before the mark", file=sys.stderr)
        return EXIT_BACKLOG
    if report.blocked_count:
        return EXIT_BACKLOG
    return EXIT_OK


def command_demo(_store: Store | None, _args: argparse.Namespace) -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        steps = demo_mod.run(Path(directory))
    for line in demo_mod.lines(steps):
        print(line)
    return EXIT_OK if all(step.ok for step in steps) else EXIT_BACKLOG


def command_selftest(_store: Store | None, args: argparse.Namespace) -> int:
    from . import selftest as selftest_mod

    return selftest_mod.run(verbose=args.verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM, description="Transactional outbox: the write and the event together."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"database ({DEFAULT_DB})")
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    place = subparsers.add_parser("place", help="place an order and append its event")
    place.add_argument("--amount", type=int, required=True)
    place.set_defaults(handler=command_place)

    pay = subparsers.add_parser("pay", help="pay an order and append its event")
    pay.add_argument("order", type=int)
    pay.set_defaults(handler=command_pay)

    show = subparsers.add_parser("show", help="print orders and events")
    show.add_argument("--pending", action="store_true", help="only unpublished events")
    show.set_defaults(handler=command_show)

    relay = subparsers.add_parser("relay", help="publish pending events")
    relay.add_argument("--limit", type=int, default=50)
    relay.add_argument(
        "--crash-after",
        type=int,
        default=None,
        metavar="N",
        help="publish N events, then die before marking the last",
    )
    relay.set_defaults(handler=command_relay)

    demo = subparsers.add_parser("demo", help="the three scenarios, on a throwaway database")
    demo.set_defaults(handler=command_demo)

    selftest = subparsers.add_parser("selftest", help="check the library without pytest")
    selftest.add_argument("--verbose", action="store_true")
    selftest.set_defaults(handler=command_selftest)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = args.handler
    if handler in (command_demo, command_selftest):
        return int(handler(None, args))
    try:
        with Store(args.db) as store:
            return int(handler(store, args))
    except (InputError, StoreError, SinkError, ValueError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
