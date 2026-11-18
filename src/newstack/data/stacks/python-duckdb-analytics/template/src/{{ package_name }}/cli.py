"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analytics import connect, describe, revenue_by, top_n, total_revenue
from .selftest import run as run_selftest


def _data_path(args) -> Path:
    return Path(getattr(args, "data", None) or "data/orders.csv")


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_rev = sub.add_parser("revenue")
    p_rev.add_argument("--by", default=None)
    p_rev.add_argument("--data", default=None)

    p_top = sub.add_parser("top-n")
    p_top.add_argument("n", type=int)
    p_top.add_argument("--data", default=None)

    p_desc = sub.add_parser("describe")
    p_desc.add_argument("--data", default=None)

    args = parser.parse_args()
    con = connect(_data_path(args))

    if args.command == "revenue":
        if args.by:
            print(json.dumps(revenue_by(con, args.by)))
        else:
            print(total_revenue(con))
    elif args.command == "top-n":
        print(json.dumps(top_n(con, args.n)))
    elif args.command == "describe":
        print(json.dumps(describe(con)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
