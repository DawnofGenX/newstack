"""Open a CSV or Parquet file as a table, and refuse to interpolate unknown names.

DuckDB cannot bind an identifier as a parameter, so a column name has to be
interpolated into the SQL string.  That is only safe after the name has been
checked against the file's own schema — :meth:`Dataset.column` is the single
gate, and everything downstream quotes what it returns.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

READERS = {".csv": "read_csv_auto", ".parquet": "read_parquet", ".json": "read_json_auto"}


class DatasetError(ValueError):
    """The file, or the request against it, cannot be served."""


def quote(identifier: str) -> str:
    """Quote an identifier for DuckDB, escaping embedded double quotes."""
    return '"' + identifier.replace('"', '""') + '"'


class Dataset:
    """One file, opened read-only, with its schema available before any query."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        suffix = self.path.suffix.lower()
        if suffix not in READERS:
            known = ", ".join(sorted(READERS))
            raise DatasetError(f"{self.path}: unsupported file type {suffix!r} (use {known})")
        if not self.path.exists():
            raise DatasetError(f"{self.path}: cannot read (no such file)")
        self._connection = duckdb.connect(":memory:")
        reader = READERS[suffix]
        self._source = f"{reader}({self.path.resolve().as_posix()!r})"
        try:
            self._columns = self._describe()
        except duckdb.Error as exc:
            raise DatasetError(f"{self.path}: cannot read ({exc})") from exc

    def _describe(self) -> list[tuple[str, str]]:
        rows = self._connection.execute(f"DESCRIBE SELECT * FROM {self._source}").fetchall()
        return [(str(row[0]), str(row[1])) for row in rows]

    @property
    def source(self) -> str:
        """The DuckDB reader expression for this file, e.g. `read_csv_auto('/tmp/x.csv')`."""
        return self._source

    @property
    def columns(self) -> list[str]:
        """Column names, in file order."""
        return [name for name, _type in self._columns]

    def column(self, name: str) -> str:
        """Return the quoted column name, or raise with the names that do exist."""
        if name not in self.columns:
            raise DatasetError(
                f"{self.path}: no column {name!r}; the file has {', '.join(self.columns)}"
            )
        return quote(name)

    def rows(self) -> int:
        """Row count of the whole file, before any filter."""
        return int(self._connection.execute(f"SELECT count(*) FROM {self._source}").fetchone()[0])

    def execute(self, sql: str) -> list[tuple]:
        """Run SQL and return every row."""
        try:
            return self._connection.execute(sql).fetchall()
        except duckdb.Error as exc:
            raise DatasetError(f"{self.path}: query failed ({exc})") from exc

    def close(self) -> None:
        """Release the in-memory database."""
        self._connection.close()

    def __enter__(self) -> Dataset:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
