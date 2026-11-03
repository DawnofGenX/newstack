import pandas as pd
import pytest

from {{ package_name }}.data import clean, summarize


def test_summarize_empty_frame():
    summary = summarize(pd.DataFrame())
    assert summary == {
        "rows": 0.0,
        "columns": 0.0,
        "numeric_columns": 0.0,
        "numeric_means": {},
    }


def test_summarize_mixed_frame():
    frame = pd.DataFrame(
        {
            "Name": ["ada", "grace", "alan"],
            "Age": [36, 45, 41],
            "Score": [1.5, 2.5, 3.5],
        }
    )

    summary = summarize(frame)

    assert summary["rows"] == 3.0
    assert summary["columns"] == 3.0
    assert summary["numeric_columns"] == 2.0
    # One mean per column: mixing a count column with a score column would be meaningless.
    assert summary["numeric_means"] == {
        "Age": pytest.approx((36 + 45 + 41) / 3),
        "Score": pytest.approx((1.5 + 2.5 + 3.5) / 3),
    }


def test_summarize_all_text_frame_has_no_numeric_means():
    summary = summarize(pd.DataFrame({"City": ["a", "b"]}))
    assert summary["numeric_columns"] == 0.0
    assert summary["numeric_means"] == {}


def test_clean_renames_columns_to_snake_case():
    frame = pd.DataFrame({"Unit Price": [1.0, 2.0], "Order ID": [10, 11]})

    cleaned = clean(frame)

    assert list(cleaned.columns) == ["unit_price", "order_id"]


def test_clean_drops_fully_empty_rows():
    frame = pd.DataFrame(
        {
            "Unit Price": [1.0, None, 3.0],
            "Order ID": [10, None, 12],
        }
    )

    cleaned = clean(frame)

    assert len(cleaned) == 2
    assert cleaned["unit_price"].tolist() == [1.0, 3.0]
    assert list(cleaned.index) == [0, 1]


def test_clean_does_not_mutate_input():
    frame = pd.DataFrame({"Unit Price": [1.0]})

    clean(frame)

    assert list(frame.columns) == ["Unit Price"]
