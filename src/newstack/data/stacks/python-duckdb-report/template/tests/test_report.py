"""The numbers are the product, so they are asserted to the digit."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from {{ package_name }}.dataset import Dataset
from {{ package_name }}.report import (
    Report,
    as_csv,
    as_json,
    as_markdown,
    build,
    render,
)

CSV = "region,revenue\nnorth,0.10\nsouth,0.20\nnorth,0.20\nwest,\neast,5.00\n"


@pytest.fixture
def dataset(tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text(CSV, encoding="utf-8")
    with Dataset(path) as opened:
        yield opened


def test_groups_are_ordered_by_total_then_name(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue")
    assert [row.group for row in report.rows] == ["east", "north", "south"]


def test_money_is_summed_as_decimals(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue")
    north = next(row for row in report.rows if row.group == "north")
    assert north.total == Decimal("0.30"), "0.10 + 0.20 must not be 0.30000000000000004"


def test_null_metrics_are_counted_not_dropped(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue")
    assert report.scanned == 5
    assert report.skipped == 1
    assert sum(row.rows for row in report.rows) == 4


def test_limit_keeps_the_largest_groups(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue", limit=2)
    assert [row.group for row in report.rows] == ["east", "north"]
    assert report.skipped == 1, "the skip count covers the file, not the page"


def test_a_filtered_out_group_is_not_a_row(tmp_path) -> None:
    path = tmp_path / "one.csv"
    path.write_text("region,revenue\nnorth,\n", encoding="utf-8")
    with Dataset(path) as dataset:
        report = build(dataset, group_by="region", metric="revenue")
    assert report.rows == []
    assert as_markdown(report).count("_no rows_") == 1


def test_markdown_is_exact(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue")
    assert as_markdown(report) == (
        "# revenue by region\n"
        "\n"
        "| region | total revenue | rows |\n"
        "| --- | ---: | ---: |\n"
        "| east | 5.00 | 1 |\n"
        "| north | 0.30 | 2 |\n"
        "| south | 0.20 | 1 |\n"
        "\n"
        "rows 5 · groups 3 · null revenue skipped 1\n"
    )


def test_json_carries_the_title_and_the_accounting(dataset) -> None:
    payload = json.loads(as_json(build(dataset, group_by="region", metric="revenue", title="t")))
    assert payload["title"] == "t"
    assert payload["scanned"] == 5
    assert payload["skipped"] == 1
    assert payload["rows"][1] == {"group": "north", "total": 0.3, "rows": 2}


def test_csv_has_a_stable_header(dataset) -> None:
    report = build(dataset, group_by="region", metric="revenue")
    assert as_csv(report).splitlines()[0] == "region,total_revenue,rows"


def test_an_unknown_format_is_a_value_error() -> None:
    with pytest.raises(ValueError, match="unknown format 'xml'"):
        render(Report(title="t", group_by="g", metric="m"), "xml")


def test_a_null_group_is_named_not_hidden(tmp_path) -> None:
    path = tmp_path / "nulls.csv"
    path.write_text("region,revenue\n,4.00\nnorth,1.00\n", encoding="utf-8")
    with Dataset(path) as dataset:
        report = build(dataset, group_by="region", metric="revenue")
    assert [row.group for row in report.rows] == ["(null)", "north"]


def test_a_parquet_copy_reports_the_same_numbers(tmp_path) -> None:
    """Same rows, different container: the report must not change."""
    import duckdb

    csv = tmp_path / "rows.csv"
    csv.write_text(CSV, encoding="utf-8")
    parquet = tmp_path / "rows.parquet"
    with duckdb.connect(":memory:") as builder:
        builder.execute(
            f"COPY (SELECT * FROM read_csv_auto({csv.as_posix()!r})) TO {parquet.as_posix()!r} "
            "(FORMAT parquet)"
        )
    csv_report = build(Dataset(csv), group_by="region", metric="revenue", title="t")
    parquet_report = build(Dataset(parquet), group_by="region", metric="revenue", title="t")
    assert as_markdown(parquet_report) == as_markdown(csv_report)
    assert parquet_report.scanned == csv_report.scanned
    assert parquet_report.skipped == csv_report.skipped
