from __future__ import annotations

import argparse
import asyncio
import sys

from .db import get_item, list_items, make_engine, seed


def _print_item(item) -> None:
    print(f"{item.id}: {item.name} {item.price}")


async def _run(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="sqlalchemy-async-api")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("list")
    get = sub.add_parser("get")
    get.add_argument("id", type=int)
    args = parser.parse_args(argv)

    if args.cmd == "init":
        engine = await make_engine("sqlite+aiosqlite:///app.db")
        n = await seed(engine)
        await engine.dispose()
        print(f"seeded {n} rows")
        return 0
    if args.cmd == "list":
        engine = await make_engine("sqlite+aiosqlite:///app.db")
        await seed(engine)
        for item in await list_items(engine):
            _print_item(item)
        await engine.dispose()
        return 0
    if args.cmd == "get":
        engine = await make_engine("sqlite+aiosqlite:///app.db")
        await seed(engine)
        item = await get_item(engine, args.id)
        await engine.dispose()
        if item is None:
            print("not found")
            return 1
        _print_item(item)
        return 0
    return 1


def _selftest() -> int:
    async def main() -> None:
        engine = await make_engine()
        n = await seed(engine)
        assert n == 3, n
        items = await list_items(engine)
        assert len(items) == 3, len(items)
        item = await get_item(engine, 1)
        assert item is not None and item.name == "widget"
        await engine.dispose()

    asyncio.run(main())
    print("selftest: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return _selftest()
    return asyncio.run(_run(argv))


if __name__ == "__main__":
    raise SystemExit(main())