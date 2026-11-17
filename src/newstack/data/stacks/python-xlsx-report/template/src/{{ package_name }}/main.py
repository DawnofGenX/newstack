"""CLI entry point."""

from __future__ import annotations

import argparse
import sys

from .report import build_report, read_csv


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()

    parser = argparse.ArgumentParser(prog="{{ package_name }}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("report")
    rp.add_argument("csv")
    rp.add_argument("out")
    ns = parser.parse_args(args)
    if ns.cmd == "report":
        rows = read_csv(ns.csv)
        build_report(rows, ns.out)
        print(f"report: {ns.out}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())