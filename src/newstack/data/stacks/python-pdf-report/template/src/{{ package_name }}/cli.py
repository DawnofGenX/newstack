"""CLI: NDJSON in, PDF out, a summary on stdout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import InputError, parse_ndjson, read_records
from .render import build_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blog-report",
        description="Render a deterministic PDF report of per-record text statistics.",
    )
    parser.add_argument("--input", default="-", help="NDJSON file, or - for stdin (default)")
    parser.add_argument("--output", default="report.pdf", help="where to write the PDF")
    parser.add_argument("--title", default="Text statistics")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--per-page", type=int, default=25, help="0 disables the table")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.input == "-":
            records = parse_ndjson(sys.stdin.read())
        else:
            records = read_records(Path(args.input))
    except InputError as error:
        print(f"blog-report: {error}", file=sys.stderr)
        return 2

    data, summary = build_report(
        records,
        title=args.title,
        subtitle=args.subtitle,
        per_page=args.per_page,
    )
    try:
        Path(args.output).write_bytes(data)
    except OSError as error:
        print(f"blog-report: {args.output}: {error.strerror}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({**summary.as_dict(), "output": args.output, "bytes_written": len(data)}))
    else:
        print(
            f"wrote {args.output} ({len(data)} bytes, {summary.pages} page(s), "
            f"{summary.records} record(s))"
        )
        if summary.unmappable:
            print(
                f"warning: {summary.unmappable} character(s) outside cp1252 replaced with '?'",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
