"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .fts import add_document, connect, ensure_schema, search


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    idx = sub.add_parser("index")
    idx.add_argument("db")
    idx.add_argument("--file", default=None)

    srch = sub.add_parser("search")
    srch.add_argument("db")
    srch.add_argument("query", nargs="+")
    srch.add_argument("--limit", type=int, default=10)

    ns = parser.parse_args(args)

    if ns.cmd == "index":
        conn = connect(ns.db)
        ensure_schema(conn)
        if ns.file:
            raw = Path(ns.file).read_text().strip()
        else:
            raw = sys.stdin.read().strip()
        if raw:
            try:
                items = json.loads(raw)
            except json.JSONDecodeError:
                items = [json.loads(line) for line in raw.splitlines() if line.strip()]
            if isinstance(items, dict):
                items = [items]
            for it in items:
                add_document(conn, int(it["id"]), it.get("title", ""), it.get("text", it.get("body", "")))
        conn.close()
        print("indexed")
        return 0

    if ns.cmd == "search":
        conn = connect(ns.db)
        ensure_schema(conn)
        results = search(conn, " ".join(ns.query), limit=ns.limit)
        for r in results:
            print(f"{r['id']}\t{r['score']:.4f}\t{r['title']}\t{r['snippet']}")
        conn.close()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())