"""Offline self-test."""

from __future__ import annotations

from pathlib import Path

from .analytics import connect, describe, top_n, total_revenue


def _data_path() -> Path:
    local = Path("data/orders.csv")
    if local.exists():
        return local
    return Path(__file__).resolve().parents[2] / "data" / "orders.csv"


def run() -> int:
    con = connect(_data_path())
    assert total_revenue(con) == 640.0
    assert top_n(con, 2)[0]["product"] == "gadget"
    assert describe(con)["rows"] == 5
    print("selftest: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
