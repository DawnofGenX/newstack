"""A self-check that needs nothing but the interpreter, so `pip install` is never a gate.

Every assertion here is about behaviour a user would notice, in the order they
would notice it: a fresh database migrates, a second run does nothing, an edited
file is refused, and a broken file leaves no debris.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from {{ package_name }}.migration import MigrationError, load
from {{ package_name }}.runner import (
    DriftError,
    MigrationFailed,
    apply,
    plan,
    split_statements,
)
from {{ package_name }}.store import Store


def run() -> int:
    """Run every check and return 0 if they all pass."""
    checks: list[str] = []

    def ok(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    def stamp() -> datetime:
        return datetime(2026, 5, 6, 7, 8, 9, tzinfo=UTC)

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        migrations = root / "migrations"
        migrations.mkdir()
        (migrations / "0001_init.sql").write_text(
            "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL);\n", encoding="utf-8"
        )
        (migrations / "0002_pinned.sql").write_text(
            "ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;\n", encoding="utf-8"
        )

        found = load(migrations)
        ids = [migration.migration_id for migration in found]
        ok(ids == ["0001", "0002"], "files load in order")
        ok(len(found[0].short()) == 12, "the short checksum is twelve characters")

        store = Store.open(root / "app.db")
        store.ensure_ledger()
        try:
            status = plan(found, store.applied())
            ok(len(status.pending) == 2, "a fresh database has two pending migrations")

            ran = apply(store, status, now=stamp)
            ok(len(ran) == 2, "both migrations ran")
            stamp_written = store.applied()["0002"].applied_at
            ok(stamp_written == "2026-05-06T07:08:09Z", "the ledger keeps the stamp it was given")
            columns = {
                str(row["name"])
                for row in store.connection.execute("PRAGMA table_info(notes)").fetchall()
            }
            ok({"id", "title", "pinned"} == columns, "the columns are the ones the files asked for")

            again = plan(load(migrations), store.applied())
            ok(again.pending == [], "a second plan is empty")
            ok(apply(store, again, now=stamp) == [], "a second apply is a no-op")

            (migrations / "0001_init.sql").write_text("-- reworded\n", encoding="utf-8")
            drifted = plan(load(migrations), store.applied())
            names = [migration.label for migration in drifted.drifted]
            ok(names == ["0001_init"], "an edit to an applied file is drift")
            try:
                apply(store, drifted, now=stamp)
            except DriftError:
                ok(True, "drift stops the run")
            else:
                ok(False, "drift stops the run")

            (migrations / "0001_init.sql").write_text(
                "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL);\n",
                encoding="utf-8",
            )
            broken = root / "broken"
            broken.mkdir()
            (broken / "0009_half.sql").write_text(
                "CREATE TABLE debris (x INTEGER);\nINSERT INTO nope VALUES (1);\n", encoding="utf-8"
            )
            try:
                apply(store, plan(load(broken), store.applied()), now=stamp)
            except MigrationFailed:
                ok(True, "a failing migration is reported")
            else:
                ok(False, "a failing migration is reported")
            debris = store.connection.execute(
                "SELECT count(*) FROM sqlite_master WHERE name = 'debris'"
            ).fetchone()[0]
            ok(debris == 0, "the failed migration left no table behind")
            ok(not store.connection.in_transaction, "the failed migration left no open transaction")
        finally:
            store.close()

        tricky = (
            "INSERT INTO notes (title) VALUES ('a; b');\n"
            "CREATE TRIGGER t AFTER UPDATE ON notes\n"
            "BEGIN\n"
            "  UPDATE notes SET title = title;\n"
            "END;\n"
        )
        statements = split_statements(tricky)
        ok(len(statements) == 2, "a semicolon in a string and one in a trigger body do not split")
        try:
            load(root / "absent")
        except MigrationError:
            ok(True, "a missing directory is an error")
        else:
            ok(False, "a missing directory is an error")

    sys.stdout.write(f"selftest: {len(checks)} checks passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
