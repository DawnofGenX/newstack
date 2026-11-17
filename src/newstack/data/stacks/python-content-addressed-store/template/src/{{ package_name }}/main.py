"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .store import Store


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("put")
    p.add_argument("store")
    p.add_argument("file")
    p.add_argument("--name", default=None)

    g = sub.add_parser("get")
    g.add_argument("store")
    g.add_argument("name")
    g.add_argument("out")

    d = sub.add_parser("delete")
    d.add_argument("store")
    d.add_argument("name")

    v = sub.add_parser("verify")
    v.add_argument("store")
    v.add_argument("--json", action="store_true", dest="as_json")

    gc = sub.add_parser("gc")
    gc.add_argument("store")

    ls = sub.add_parser("list")
    ls.add_argument("store")

    ns = parser.parse_args(args)
    store = Store(ns.store)

    if ns.cmd == "put":
        digest = store.put_file(ns.file, name=ns.name)
        print(digest)
        return 0
    if ns.cmd == "get":
        Path(ns.out).write_bytes(store.get(ns.name))
        return 0
    if ns.cmd == "delete":
        store.delete(ns.name)
        return 0
    if ns.cmd == "verify":
        res = store.verify()
        if ns.as_json:
            print(json.dumps(res, indent=2))
        else:
            print("OK" if res["ok"] else "FAIL")
            for e in res["errors"]:
                print(e)
        return 0 if res["ok"] else 1
    if ns.cmd == "gc":
        freed = store.gc()
        print(f"freed {freed} bytes")
        return 0
    if ns.cmd == "list":
        for n, h in sorted(store._manifest.items()):
            print(f"{n}\t{h}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())