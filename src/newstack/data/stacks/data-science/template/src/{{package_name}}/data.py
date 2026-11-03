"""Typed helpers for small, in-memory pandas frames."""

from __future__ import annotations

import re

import pandas as pd

_SEPARATORS = re.compile(r"[^0-9A-Za-z]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _snake_case(name: str) -> str:
    """Convert an arbitrary column label to ``snake_case``."""
    text = _CAMEL_BOUNDARY.sub("_", name.strip())
    text = _SEPARATORS.sub("_", text).strip("_")
    return text.lower()


def summarize(frame: pd.DataFrame) -> dict[str, object]:
    """Return row/column counts and a mean *per numeric column*.

    Deliberately per column: averaging every numeric column together mixes units
    (a count of 12 and a revenue of 120.5) and produces a number with no meaning.
    """
    numeric = frame.select_dtypes(include="number")
    return {
        "rows": float(frame.shape[0]),
        "columns": float(frame.shape[1]),
        "numeric_columns": float(numeric.shape[1]),
        "numeric_means": {
            str(column): float(numeric[column].mean()) for column in numeric.columns
        },
    }


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with all-empty rows dropped and column names normalised.

    Column labels are stripped and converted to ``snake_case`` for stable
    attribute access (``"Unit Price"`` becomes ``"unit_price"``). The input
    frame is never mutated.
    """
    result = frame.dropna(how="all").copy()
    result.columns = [_snake_case(str(column)) for column in result.columns]
    return result.reset_index(drop=True)
