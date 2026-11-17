from __future__ import annotations

from pathlib import Path

import polars as pl


def transform(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("value") >= 0).with_columns(
        (pl.col("value") * 2).alias("doubled")
    )


def run_pipeline(src: Path, dst: Path) -> int:
    frame = pl.read_parquet(src)
    result = transform(frame)
    dst.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(dst)
    return result.height