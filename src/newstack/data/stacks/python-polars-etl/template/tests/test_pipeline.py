import polars as pl

from {{ package_name }}.pipeline import run_pipeline, transform


def test_transform_filters_and_doubles():
    df = pl.DataFrame({"value": [1, -2, 3]})
    out = transform(df)
    assert out["value"].to_list() == [1, 3]
    assert out["doubled"].to_list() == [2, 6]


def test_run_pipeline_roundtrip(tmp_path):
    src = tmp_path / "in.parquet"
    dst = tmp_path / "out.parquet"
    pl.DataFrame({"value": [5, -1, 0]}).write_parquet(src)
    rows = run_pipeline(src, dst)
    assert rows == 2
    assert dst.is_file()
