"""Offline contract check: `python -m {{ package_name }} --selftest`."""

from __future__ import annotations

import csv
import os
import tempfile

from .importer import import_csv


def run() -> int:
    d = tempfile.mkdtemp()
    csv_path = os.path.join(d, "data.csv")
    db_path = os.path.join(d, "out.db")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "qty"])
        w.writerow(["1", "alpha", "2"])
        w.writerow(["2", "beta", "3"])
        w.writerow(["bad", "gamma", "x"])  # coercion error on qty? id int? id stays text default; qty int fails
    report = import_csv(csv_path, db_path, mapping={"id": "id:int", "name": "name:text", "qty": "qty:int"}, key="id")
    assert report.inserted == 2, report
    assert len(report.errors) == 1
    # re-run is idempotent
    report2 = import_csv(csv_path, db_path, mapping={"id": "id:int", "name": "name:text", "qty": "qty:int"}, key="id")
    assert report2.inserted + report2.updated == 2
    # dry-run writes nothing new
    rep_dry = import_csv(csv_path, db_path, mapping={"id": "id:int", "name": "name:text", "qty": "qty:int"}, key="id", dry_run=True)
    assert rep_dry.inserted == 2
    import sqlite3
    # dry_run target db unchanged count
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 2
    conn.close()
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())