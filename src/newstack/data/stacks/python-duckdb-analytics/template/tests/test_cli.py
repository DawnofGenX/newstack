from pathlib import Path

from {{ package_name }}.analytics import connect, describe, top_n, total_revenue


def test_total_revenue() -> None:
    con = connect(Path("data/orders.csv"))
    assert total_revenue(con) == 640.0


def test_top_n() -> None:
    con = connect(Path("data/orders.csv"))
    rows = top_n(con, 2)
    assert rows[0] == {"product": "gadget", "revenue": 370}
    assert rows[1] == {"product": "widget", "revenue": 270}


def test_describe() -> None:
    con = connect(Path("data/orders.csv"))
    d = describe(con)
    assert d["rows"] == 5
    assert "revenue" in d["columns"]
