"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import extract_cards, extract_tables, tables_to_csv
from .selftest import run as run_selftest


def main() -> int:
    if "--selftest" in sys.argv:
        return run_selftest()

    parser = argparse.ArgumentParser(prog="bs4-scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("tables", help="Extract tables as JSON or CSV")
    t.add_argument("file")
    t.add_argument("--format", choices=["json", "csv"], default="json")

    c = sub.add_parser("cards", help="Extract cards as JSON")
    c.add_argument("file")

    args = parser.parse_args()
    html = Path(args.file).read_text(encoding="utf-8")

    if args.command == "tables":
        tables = extract_tables(html)
        if args.format == "csv":
            print(tables_to_csv(tables), end="")
        else:
            print(json.dumps(tables))
    elif args.command == "cards":
        print(json.dumps(extract_cards(html)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
