"""The command line: seed, page, scan, demo, selftest."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import selftest as selftest_mod
from .demo import run as run_demo
from .model import KEYS, InputError, Order, Query
from .pager import duplicates, missing, page, scan
from .store import Store, StoreError

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_UNUSABLE = 2
DEFAULT_DB = Path("items.db")


def add_query_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--order", default="created_at", choices=KEYS, help="sort key")
    parser.add_argument("--desc", action="store_true", help="walk the order backwards")
    parser.add_argument("--prefix", default="", help="only titles starting with this")


def query_of(args: argparse.Namespace) -> Query:
    return Query(Order(args.order, args.desc), args.prefix)


def row_line(row: dict[str, object]) -> str:
    return f"{int(row['id']):>4}  {row['created_at']}  {row['title']}"


def command_seed(store: Store | None, args: argparse.Namespace) -> int:
    assert store is not None
    ids = store.seed(args.count, rng_seed=args.rng_seed)
    print(f"seeded {len(ids)} item(s) into {store.path}")
    return EXIT_OK


def command_page(store: Store | None, args: argparse.Namespace) -> int:
    assert store is not None
    current = page(store, query_of(args), cursor=args.cursor, size=args.size)
    if args.json:
        print(json.dumps(current.as_dict(), indent=2))
        return EXIT_OK
    for row in current.rows:
        print(row_line(row))
    tail = current.next_cursor or "-"
    print(f"page    {current.size} row(s); next {tail}")
    return EXIT_OK


def command_scan(store: Store | None, args: argparse.Namespace) -> int:
    assert store is not None
    query = query_of(args)
    seen = scan(store, query, size=args.size)
    expected = store.ordered_ids(query)
    repeated = duplicates(seen)
    absent = missing(seen, expected)
    if args.json:
        print(json.dumps({"ids": seen, "duplicates": repeated, "missing": absent}, indent=2))
    else:
        print(" ".join(str(ident) for ident in seen))
        print(f"scanned {len(seen)} row(s), {len(repeated)} duplicate(s), {len(absent)} missing")
    return EXIT_PROBLEM if repeated or absent else EXIT_OK


def command_demo(store: Store | None, args: argparse.Namespace) -> int:
    del store
    with tempfile.TemporaryDirectory() as directory:
        steps = run_demo(Path(directory))
    for step in steps:
        print(step.render())
        for line in step.lines():
            print(f"    {line}")
    broken = [step for step in steps if not step.keyset_clean]
    quiet = [step for step in steps if not step.offset_broken]
    print(
        f"demo: {len(steps)} scenarios, {len(broken)} cursor problem(s), "
        f"{len(quiet)} offset walk(s) that survived"
    )
    return EXIT_PROBLEM if broken or quiet else EXIT_OK


def command_selftest(store: Store | None, args: argparse.Namespace) -> int:
    del store, args
    return selftest_mod.run()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Keyset pagination: cursors that cannot skip or repeat a row.",
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB, help=f"database (default {DEFAULT_DB})"
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="create a deterministic population")
    seed.add_argument("--count", type=int, default=30)
    seed.add_argument("--rng-seed", type=int, default=7)
    seed.set_defaults(handler=command_seed)

    one = sub.add_parser("page", help="fetch one page")
    one.add_argument("--size", type=int, default=20)
    one.add_argument("--cursor", default=None)
    one.add_argument("--json", action="store_true")
    add_query_arguments(one)
    one.set_defaults(handler=command_page)

    walk = sub.add_parser("scan", help="page through everything and report duplicates")
    walk.add_argument("--size", type=int, default=20)
    walk.add_argument("--json", action="store_true")
    add_query_arguments(walk)
    walk.set_defaults(handler=command_scan)

    demo = sub.add_parser("demo", help="show what a deletion does to OFFSET")
    demo.set_defaults(handler=command_demo)

    self_check = sub.add_parser("selftest", help="check the machinery without pytest")
    self_check.set_defaults(handler=command_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.handler in (command_demo, command_selftest):
            return int(args.handler(None, args))
        with Store(args.db) as store:
            return int(args.handler(store, args))
    except (InputError, StoreError, OSError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
