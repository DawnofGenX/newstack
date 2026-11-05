"""Offline checks over a temporary CSV: no network, no files left behind."""

from __future__ import annotations

import tempfile
from decimal import Decimal
from pathlib import Path

from {{ package_name }}.dataset import Dataset, DatasetError, quote
from {{ package_name }}.report import (
    Report,
    as_csv,
    as_json,
    as_markdown,
    build,
    render,
)

CSV = "region,revenue\nnorth,10.10\nsouth,20.20\nnorth,0.05\nwest,\n"


def run() -> int:
    """Return 0 when every check passed."""
    checks = 0

    def ok(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise SystemExit(f"selftest: FAIL {label}")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "tiny.csv"
        path.write_text(CSV, encoding="utf-8")
        with Dataset(path) as dataset:
            ok(dataset.columns == ["region", "revenue"], "columns keep file order")
            ok(dataset.rows() == 4, "every row is counted, including the null one")
            ok(dataset.column("region") == '"region"', "identifiers are quoted")
            try:
                dataset.column("nope")
            except DatasetError as exc:
                ok("no column 'nope'" in str(exc), "an unknown column is refused")
                ok("region, revenue" in str(exc), "the message lists the real columns")
            else:
                ok(False, "an unknown column is refused")

            report = build(dataset, group_by="region", metric="revenue")
            ok([row.group for row in report.rows] == ["south", "north"], "largest first")
            ok(report.rows[1].rows == 2, "groups count their rows")
            ok(report.rows[1].total == Decimal("10.15"), "money is exact: 10.15, not 10.1499…")
            ok(report.scanned == 4 and report.skipped == 1, "the null row is reported, not dropped")

            markdown = as_markdown(report)
            ok(markdown.startswith("# revenue by region\n"), "the title names metric and group")
            ok("| --- | ---: | ---: |" in markdown, "numbers are right aligned")
            ok("| south | 20.20 | 1 |" in markdown, "money is rendered with two decimals")
            ok(markdown.endswith("null revenue skipped 1\n"), "the footer accounts for nulls")

            ok('"skipped": 1' in as_json(report), "JSON carries the skip count")
            header = as_csv(report).splitlines()[0]
            ok(header == "region,total_revenue,rows", "CSV header is stable")
            ok(render(report, "md") == markdown, "render() matches as_markdown()")

    try:
        render(Report(title="t", group_by="g", metric="m"), "xml")
    except ValueError as exc:
        ok("unknown format" in str(exc), "an unknown format is refused")
    except KeyError:
        ok(False, "an unknown format is refused")
    else:
        ok(False, "an unknown format is refused")

    ok(quote('we"ird') == '"we""ird"', 'embedded quotes are doubled')

    print(f"selftest: {checks} checks passed")
    return 0
