"""The rules that stop a database from quietly disagreeing with the repository."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from {{ package_name }}.migration import MigrationError, load
from {{ package_name }}.runner import (
    DriftError,
    MigrationFailed,
    OutOfOrderError,
    apply,
    plan,
    split_statements,
)
from {{ package_name }}.store import Store

INIT = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL);\n"


def write(folder, name: str, sql: str):
    (folder / name).write_text(sql, encoding="utf-8")


@pytest.fixture
def store(tmp_path):
    opened = Store.open(tmp_path / "app.db")
    opened.ensure_ledger()
    yield opened
    opened.close()


@pytest.fixture
def migrations_dir(tmp_path):
    folder = tmp_path / "migrations"
    folder.mkdir()
    write(folder, "0001_init.sql", INIT)
    write(folder, "0002_title_index.sql", "CREATE INDEX notes_by_title ON notes (title);\n")
    return folder


def fixed_now() -> datetime:
    return datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


def test_plan_marks_everything_pending_on_a_fresh_database(store, migrations_dir) -> None:
    status = plan(load(migrations_dir), store.applied())
    assert [step.state for step in status.steps] == ["pending", "pending"]
    assert [migration.slug for migration in status.pending] == ["init", "title_index"]


def test_plan_marks_a_matching_checksum_applied(store, migrations_dir) -> None:
    status = plan(load(migrations_dir), store.applied())
    apply(store, status, now=fixed_now)
    again = plan(load(migrations_dir), store.applied())
    assert [step.state for step in again.steps] == ["applied", "applied"]
    assert again.pending == []


def test_plan_marks_an_edited_file_drifted(store, migrations_dir) -> None:
    apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now)
    write(migrations_dir, "0001_init.sql", INIT + "-- edited after it ran\n")
    status = plan(load(migrations_dir), store.applied())
    assert [step.state for step in status.steps] == ["drifted", "applied"]
    assert [migration.slug for migration in status.drifted] == ["init"]


def test_apply_runs_pending_in_order(store, migrations_dir) -> None:
    ran = apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now)
    assert [migration.label for migration in ran] == ["0001_init", "0002_title_index"]
    tables = store.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'notes_by_title'"
    ).fetchall()
    assert len(tables) == 1


def test_apply_is_idempotent(store, migrations_dir) -> None:
    apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now)
    assert apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now) == []


def test_the_ledger_keeps_the_checksum_and_the_stamp(store, migrations_dir) -> None:
    apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now)
    first = store.applied()["0001"]
    assert first.checksum == load(migrations_dir)[0].checksum
    assert first.applied_at == "2026-01-02T03:04:05Z"


def test_drift_blocks_every_migration(store, migrations_dir) -> None:
    apply(store, plan(load(migrations_dir), store.applied()), now=fixed_now)
    write(migrations_dir, "0001_init.sql", INIT + "-- edited\n")
    write(migrations_dir, "0003_late.sql", "ALTER TABLE notes ADD COLUMN late INTEGER;\n")
    status = plan(load(migrations_dir), store.applied())
    with pytest.raises(DriftError, match="modified after being applied: 0001_init"):
        apply(store, status, now=fixed_now)
    assert "0003" not in store.applied(), "a drifted ledger must not let new work through"


def test_a_pending_migration_older_than_the_ledger_is_refused(store, tmp_path) -> None:
    folder = tmp_path / "gappy"
    folder.mkdir()
    write(folder, "0001_init.sql", INIT)
    write(folder, "0003_late.sql", "ALTER TABLE notes ADD COLUMN late INTEGER;\n")
    apply(store, plan(load(folder), store.applied()), now=fixed_now)
    write(folder, "0002_halfway.sql", "ALTER TABLE notes ADD COLUMN halfway INTEGER;\n")
    status = plan(load(folder), store.applied())
    with pytest.raises(OutOfOrderError) as caught:
        apply(store, status, now=fixed_now)
    assert "0002_halfway is pending but 0003_late is already applied" in str(caught.value)


def test_a_failing_migration_rolls_back_its_own_statements(store, tmp_path) -> None:
    folder = tmp_path / "broken"
    folder.mkdir()
    write(
        folder,
        "0001_half.sql",
        "CREATE TABLE partial (id INTEGER);\nINSERT INTO nope VALUES (1);\n",
    )
    with pytest.raises(MigrationFailed, match="nothing from this file was applied"):
        apply(store, plan(load(folder), store.applied()), now=fixed_now)
    tables = store.connection.execute(
        "SELECT name FROM sqlite_master WHERE name = 'partial'"
    ).fetchall()
    assert tables == [], "the CREATE TABLE before the failure must be rolled back"


def test_a_failing_migration_writes_no_ledger_row(store, tmp_path) -> None:
    folder = tmp_path / "broken"
    folder.mkdir()
    write(folder, "0001_half.sql", "INSERT INTO nope VALUES (1);\n")
    with pytest.raises(MigrationFailed):
        apply(store, plan(load(folder), store.applied()), now=fixed_now)
    assert store.applied() == {}
    assert not store.connection.in_transaction, "the transaction must be closed, not left open"


def test_a_trigger_body_stays_one_statement() -> None:
    script = (
        "CREATE TRIGGER touch AFTER UPDATE ON notes\n"
        "BEGIN\n"
        "    UPDATE notes SET title = title WHERE id = NEW.id;\n"
        "END;\n"
    )
    statements = split_statements(script)
    assert len(statements) == 1
    assert statements[0].endswith("END;")


def test_a_semicolon_inside_a_string_is_not_a_boundary() -> None:
    statements = split_statements("INSERT INTO notes (title) VALUES ('one; two');\n")
    assert len(statements) == 1


def test_an_unterminated_statement_is_an_error() -> None:
    with pytest.raises(MigrationError, match="unterminated statement"):
        split_statements("CREATE TABLE t (x INTEGER)\n")


def test_comments_do_not_become_statements() -> None:
    assert split_statements("-- just a note\n") == []


def test_sqlite_autocommits_ddl_without_an_explicit_transaction(tmp_path) -> None:
    """The reason every migration opens `BEGIN` itself.

    The sqlite3 module's default isolation level opens no transaction around DDL,
    so `with connection:` cannot roll a failed `CREATE TABLE` back. This test
    records the trap so that nobody "simplifies" the runner into it.
    """
    connection = sqlite3.connect(tmp_path / "trap.db")
    with pytest.raises(sqlite3.Error), connection:
        connection.execute("CREATE TABLE kept (x INTEGER)")
        connection.execute("CREATE TABLE kept (x INTEGER)")
    survived = connection.execute(
        "SELECT count(*) FROM sqlite_master WHERE name = 'kept'"
    ).fetchone()[0]
    connection.close()
    assert survived == 1, "the first statement was committed before the exception"
