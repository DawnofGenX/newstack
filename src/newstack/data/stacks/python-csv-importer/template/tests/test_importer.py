"""Tests for the CSV importer."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from {{ package_name }}.importer import import_csv


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)


def test_import_basic(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    db_path = tmp_path / "out.db"
    _write_csv(csv_path, [["id", "name", "qty"], ["1", "alpha", "2"], ["2", "beta", "3"]])
    report = import_csv(csv_path, db_path, mapping={"id": "id:int", "name": "name:text", "qty": "qty:int"}, key="id")
    assert report.inserted == 2
    assert report.errors == []
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 2
    conn.close()


def test_malformed_row_reports_line(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    db_path = tmp_path / "out.db"
    _write_csv(csv_path, [["id", "name", "qty"], ["1", "alpha", "2"], ["2", "beta", "nope"], ["3", "gamma", "4"]])
    report = import_csv(csv_path, db_path, mapping={"id": "id:int", "name": "name:text", "qty": "qty:int"}, key="id")
    assert report.inserted == 2
    assert len(report.errors) == 1
    assert report.errors[0].line == 3


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    db_path = tmp_path / "out.db"
    _write_csv(csv_path, [["id", "name"], ["1", "alpha"]])
    report = import_csv(csv_path, db_path, dry_run=True)
    assert report.inserted == 1
    assert not db_path.exists()


def test_rerun_does_not_duplicate(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    db_path = tmp_path / "out.db"
    _write_csv(csv_path, [["id", "name"], ["1", "alpha"], ["2", "beta"]])
    import_csv(csv_path, db_path, key="id")
    import_csv(csv_path, db_path, key="id")
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 2
    conn.close()


def test_header_mapping(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    db_path = tmp_path / "out.db"
    _write_csv(csv_path, [["A", "B"], ["1", "x"]])
    report = import_csv(csv_path, db_path, mapping={"A": "id:int", "B": "name:text"}, key="id")
    assert report.inserted == 1
    conn = sqlite3.connect(db_path)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(records)").fetchall()]
    assert "id" in cols and "name" in cols
    conn.close()