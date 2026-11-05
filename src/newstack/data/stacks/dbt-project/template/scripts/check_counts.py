"""Read the built mart and assert the numbers, independent of dbt's own test runner."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

EXPECTED = {
    1: (1, 2, 12),
    2: (2, 3, 6),
    3: (1, 1, 11),
    4: (1, 2, 14),
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    database = root / "target" / "{{ package_name }}.duckdb"
    if not database.exists():
        print(f"missing {database}; run dbt build first", file=sys.stderr)
        return 1
    rows = duckdb.connect(str(database), read_only=True).execute(
        "select id, lines, words, bytes from main_marts.doc_stats order by id"
    ).fetchall()
    failures = []
    for row in rows:
        doc_id, lines, words, bytes_ = row
        expected = EXPECTED.get(doc_id)
        if expected is None:
            failures.append(f"unexpected row id={doc_id}")
        elif (lines, words, bytes_) != expected:
            failures.append(f"id={doc_id}: expected {expected}, got {(lines, words, bytes_)}")
    if len(rows) != len(EXPECTED):
        failures.append(f"expected {len(EXPECTED)} rows, got {len(rows)}")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(f"{len(rows)} rows match the documented counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
