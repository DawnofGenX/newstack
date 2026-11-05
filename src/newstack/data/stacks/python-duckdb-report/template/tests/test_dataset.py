"""The dataset is the single gate for identifiers, so it gets the strict tests."""

from __future__ import annotations

import pytest

from {{ package_name }}.dataset import Dataset, DatasetError, quote

CSV = "region,revenue\nnorth,1.10\nsouth,\n"


@pytest.fixture
def dataset(tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text(CSV, encoding="utf-8")
    with Dataset(path) as opened:
        yield opened


def test_columns_keep_file_order(dataset) -> None:
    assert dataset.columns == ["region", "revenue"]


def test_rows_counts_every_line_including_nulls(dataset) -> None:
    assert dataset.rows() == 2


def test_known_columns_are_quoted(dataset) -> None:
    assert dataset.column("revenue") == '"revenue"'


def test_an_unknown_column_names_the_ones_that_exist(dataset) -> None:
    with pytest.raises(DatasetError) as caught:
        dataset.column("revenu")
    assert "no column 'revenu'" in str(caught.value)
    assert "region, revenue" in str(caught.value)


def test_the_source_expression_uses_the_right_reader(dataset) -> None:
    assert dataset.source.startswith("read_csv_auto(")
    assert dataset.source.endswith(".csv')")


def test_an_unsupported_suffix_is_refused_before_duckdb_sees_it(tmp_path) -> None:
    path = tmp_path / "rows.txt"
    path.write_text(CSV, encoding="utf-8")
    with pytest.raises(DatasetError, match=r"unsupported file type '\.txt'"):
        Dataset(path)


def test_a_missing_file_says_so(tmp_path) -> None:
    with pytest.raises(DatasetError, match="no such file"):
        Dataset(tmp_path / "nope.csv")


@pytest.mark.parametrize(("raw", "quoted"), [("plain", '"plain"'), ('we"ird', '"we""ird"')])
def test_quote_doubles_embedded_quotes(raw, quoted) -> None:
    assert quote(raw) == quoted


def test_parquet_is_read_with_the_parquet_reader(tmp_path) -> None:
    """Parquet is claimed in the blurb, so it is proven the same way CSV is."""
    import duckdb

    csv = tmp_path / "rows.csv"
    csv.write_text(CSV, encoding="utf-8")
    parquet = tmp_path / "rows.parquet"
    # `with` matters: an unclosed duckdb connection is collected at a random moment,
    # and a ResourceWarning raised mid-test is an error under `filterwarnings = error`.
    with duckdb.connect(":memory:") as builder:
        builder.execute(
            f"COPY (SELECT * FROM read_csv_auto({csv.as_posix()!r})) TO {parquet.as_posix()!r} "
            "(FORMAT parquet)"
        )
    with Dataset(parquet) as opened:
        assert opened.source.startswith("read_parquet(")
        assert opened.columns == ["region", "revenue"]
        assert opened.rows() == 2
