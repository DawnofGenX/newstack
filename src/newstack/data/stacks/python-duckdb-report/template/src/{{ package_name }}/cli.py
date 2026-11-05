"""Report a file's numbers from the command line.

Exit codes: 0 a report was produced, 2 the file or the request cannot be served.
Nothing returns 1 — a report over bad input is not a partial success.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from {{ package_name }} import __version__
from {{ package_name }}.dataset import Dataset, DatasetError
from {{ package_name }}.report import FORMATS, build, render

EXIT_OK = 0
EXIT_UNUSABLE = 2


def build_parser() -> argparse.ArgumentParser:
    """The CLI surface, described once."""
    parser = argparse.ArgumentParser(
        prog="{{ npm_name }}",
        description="Deterministic reports over CSV and Parquet files, via DuckDB.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="sum one column per group")
    report.add_argument("--data", required=True, help="CSV, Parquet or JSON file")
    report.add_argument("--group-by", required=True, help="column to group by")
    report.add_argument("--metric", required=True, help="numeric column to sum")
    report.add_argument("--title", default="", help="heading for the markdown report")
    report.add_argument("--limit", type=int, default=0, help="keep only the top N groups")
    report.add_argument("--format", default="md", help=f"one of {', '.join(FORMATS)}")
    report.add_argument("--out", default="-", help="write here instead of stdout")

    sub.add_parser("selftest", help="run the offline checks")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse, query, render. A bad file or column exits 2 with a readable message."""
    args = build_parser().parse_args(argv)
    if args.command == "selftest":
        from {{ package_name }}.selftest import run as selftest

        return selftest()

    if args.format not in FORMATS:
        known = ", ".join(FORMATS)
        print(f"error: unknown format {args.format!r}; choose {known}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        with Dataset(args.data) as dataset:
            report = build(
                dataset,
                group_by=args.group_by,
                metric=args.metric,
                limit=args.limit,
                title=args.title,
            )
    except DatasetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE

    text = render(report, args.format)
    if args.out == "-":
        sys.stdout.write(text)
    else:
        try:
            Path(args.out).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"error: {args.out}: cannot write ({exc.strerror})", file=sys.stderr)
            return EXIT_UNUSABLE
    return EXIT_OK
