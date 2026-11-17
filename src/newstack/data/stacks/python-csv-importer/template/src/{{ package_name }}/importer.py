"""CSV to SQLite importer with header mapping, coercion and idempotent upserts."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RowError:
    line: int
    message: str


@dataclass
class ImportReport:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[RowError] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": [{"line": e.line, "message": e.message} for e in self.errors],
        }


COERCERS: dict[str, Callable[[str], Any]] = {
    "text": lambda v: v,
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "bool": lambda v: v.strip().lower() in {"1", "true", "yes", "y", "on"},
}


def _parse_mapping(raw: Any) -> dict[str, tuple[str, str]]:
    """Mapping: source header -> (target column, type)."""
    if raw is None:
        return {}
    if isinstance(raw, str):
        raw = json.loads(raw)
    result: dict[str, tuple[str, str]] = {}
    for src, spec in raw.items():
        if isinstance(spec, str):
            if ":" in spec:
                col, typ = spec.split(":", 1)
            else:
                col, typ = spec, "text"
        elif isinstance(spec, dict):
            col = spec.get("column", src)
            typ = spec.get("type", "text")
        else:
            raise TypeError(f"bad mapping for {src!r}")
        if typ not in COERCERS:
            raise ValueError(f"unknown type {typ!r}")
        result[src] = (col, typ)
    return result


def _default_mapping(headers: list[str]) -> dict[str, tuple[str, str]]:
    return {h: (h, "text") for h in headers}


def import_csv(
    csv_path: str | Path,
    db_path: str | Path,
    *,
    mapping: str | dict | None = None,
    key: str | None = None,
    dry_run: bool = False,
) -> ImportReport:
    report = ImportReport()
    csv_path = Path(csv_path)
    db_path = Path(db_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return report
        parsed_mapping = _parse_mapping(mapping) if mapping is not None else _default_mapping(headers)
        for src in parsed_mapping:
            if src not in headers:
                raise ValueError(f"CSV missing mapped source column {src!r}")
        idx = {h: i for i, h in enumerate(headers)}
        ordered_sources = [h for h in headers if h in parsed_mapping]
        targets = [parsed_mapping[h][0] for h in ordered_sources]
        types = [parsed_mapping[h][1] for h in ordered_sources]

        if key is None:
            key = targets[0] if targets else None

        rows_to_insert: list[tuple[Any, ...]] = []
        for row in reader:
            line_no = reader.line_num
            if not row:
                continue
            if len(row) != len(headers):
                report.errors.append(
                    RowError(line_no, f"expected {len(headers)} columns, got {len(row)}")
                )
                report.skipped += 1
                continue
            values: list[Any] = []
            ok = True
            for src, typ in zip(ordered_sources, types):
                raw = row[idx[src]]
                try:
                    values.append(COERCERS[typ](raw))
                except (ValueError, TypeError) as exc:
                    report.errors.append(
                        RowError(line_no, f"column {src!r}: {exc}")
                    )
                    ok = False
                    break
            if not ok:
                report.skipped += 1
                continue
            rows_to_insert.append(tuple(values))

    if dry_run:
        report.inserted += len(rows_to_insert)
        return report

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        create_sql = (
            "CREATE TABLE IF NOT EXISTS records ("
            + ", ".join(f'"{c}"' for c in targets)
            + ")"
        )
        conn.execute(create_sql)
        if key is not None:
            conn.execute(
                f'CREATE UNIQUE INDEX IF NOT EXISTS "records_{key}_uq" ON records ("{key}")'
            )
        conn.commit()

        with conn:
            for values in rows_to_insert:
                placeholders = ", ".join("?" for _ in values)
                cols = ", ".join(f'"{c}"' for c in targets)
                update_cols = [c for c in targets if c != key]
                if key is not None and update_cols:
                    set_clause = ", ".join(f'"{c}"=excluded."{c}"' for c in update_cols)
                    sql = (
                        f'INSERT INTO records ({cols}) VALUES ({placeholders}) '
                        f'ON CONFLICT("{key}") DO UPDATE SET {set_clause}'
                    )
                elif key is not None:
                    sql = (
                        f'INSERT INTO records ({cols}) VALUES ({placeholders}) '
                        f'ON CONFLICT("{key}") DO NOTHING'
                    )
                else:
                    sql = f'INSERT INTO records ({cols}) VALUES ({placeholders})'
                cur = conn.execute(sql, values)
                if cur.rowcount == 1:
                    report.inserted += 1
                else:
                    report.updated += 1
        return report
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="csv-importer")
    parser.add_argument("csv", help="input CSV file")
    parser.add_argument("db", help="output SQLite database")
    parser.add_argument("--key", help="natural key column")
    parser.add_argument("--mapping", help="JSON mapping file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    mapping = None
    if args.mapping:
        mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))

    report = import_csv(args.csv, args.db, mapping=mapping, key=args.key, dry_run=args.dry_run)
    print(json.dumps(report.as_dict(), indent=2))
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())