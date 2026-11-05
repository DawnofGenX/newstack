"""Aggregate a file and render it in a form that diffs cleanly.

Two rules make the output trustworthy:

* money is summed as ``DECIMAL``, never as a binary float — ``0.1 + 0.2`` is not
  ``0.3`` and a report that is off in the last digit is worse than no report;
* rows whose metric is null are counted and reported, not silently dropped, so
  "sum of revenue" cannot quietly become "sum of the revenue we could parse".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from {{ package_name }}.dataset import Dataset

NULL_GROUP = "(null)"
FORMATS = ("md", "json", "csv")


@dataclass(frozen=True)
class Row:
    """One group's aggregate."""

    group: str
    total: Decimal
    rows: int


@dataclass(frozen=True)
class Report:
    """The whole answer, including what was left out."""

    title: str
    group_by: str
    metric: str
    rows: list[Row] = field(default_factory=list)
    scanned: int = 0
    skipped: int = 0


def build(
    dataset: Dataset,
    *,
    group_by: str,
    metric: str,
    limit: int = 0,
    title: str = "",
) -> Report:
    """Sum ``metric`` per ``group_by``, largest first, ties broken by the group name."""
    group_column = dataset.column(group_by)
    metric_column = dataset.column(metric)
    source = dataset.source
    sql = (
        f"SELECT COALESCE(CAST({group_column} AS VARCHAR), '{NULL_GROUP}') AS g, "
        f"SUM(CAST({metric_column} AS DECIMAL(18, 4))) AS total, "
        f"count(*) AS n "
        f"FROM {source} WHERE {metric_column} IS NOT NULL "
        f"GROUP BY 1 ORDER BY total DESC NULLS LAST, g ASC"
    )
    if limit > 0:
        sql += f" LIMIT {int(limit)}"
    rows = [
        Row(group=str(group), total=Decimal(str(total)), rows=int(count))
        for group, total, count in dataset.execute(sql)
    ]
    skipped = int(
        dataset.execute(
            f"SELECT count(*) FROM {source} WHERE {metric_column} IS NULL"
        )[0][0]
    )
    return Report(
        title=title or f"{metric} by {group_by}",
        group_by=group_by,
        metric=metric,
        rows=rows,
        scanned=dataset.rows(),
        skipped=skipped,
    )


def _money(value: Decimal) -> str:
    return f"{value:,.2f}"


def as_markdown(report: Report) -> str:
    """A markdown table with right-aligned numbers and an accounting footer."""
    lines = [
        f"# {report.title}",
        "",
        f"| {report.group_by} | total {report.metric} | rows |",
        "| --- | ---: | ---: |",
    ]
    for row in report.rows:
        lines.append(f"| {row.group} | {_money(row.total)} | {row.rows} |")
    if not report.rows:
        lines.append("| _no rows_ | 0.00 | 0 |")
    lines.append("")
    lines.append(
        f"rows {report.scanned} · groups {len(report.rows)} · "
        f"null {report.metric} skipped {report.skipped}"
    )
    return "\n".join(lines) + "\n"


def as_json(report: Report) -> str:
    """The same numbers as JSON, with every field explicitly named."""
    import json

    payload = {
        "title": report.title,
        "group_by": report.group_by,
        "metric": report.metric,
        "rows": [
            {"group": row.group, "total": round(float(row.total), 6), "rows": row.rows}
            for row in report.rows
        ],
        "scanned": report.scanned,
        "skipped": report.skipped,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def as_csv(report: Report) -> str:
    """The same numbers as CSV, for a spreadsheet."""
    lines = [f"{report.group_by},total_{report.metric},rows"]
    for row in report.rows:
        lines.append(f"{row.group},{_money(row.total)},{row.rows}")
    return "\n".join(lines) + "\n"


RENDERERS = {"md": as_markdown, "json": as_json, "csv": as_csv}


def render(report: Report, fmt: str = "md") -> str:
    """Render in one of :data:`FORMATS`."""
    if fmt not in RENDERERS:
        raise ValueError(f"unknown format {fmt!r}; choose one of {', '.join(FORMATS)}")
    return RENDERERS[fmt](report)
