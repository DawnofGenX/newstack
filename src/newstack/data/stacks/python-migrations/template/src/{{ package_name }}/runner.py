"""Plan, refuse, and only then apply.

Three rules, each one a mistake that has bitten a real deployment:

1. An applied migration whose bytes changed is *drift*. Nothing runs until a human
   decides what the database should look like, because the alternative is a
   database that matches neither the file nor the ledger.
2. A pending migration numbered below the newest applied one is *out of order*.
   Applying it late gives an existing database a different history than a fresh
   one built from the same directory — the worst kind of difference, because both
   look fine on their own.
3. A migration is one transaction. Not one transaction per statement, and not
   ``executescript`` — see :func:`split_statements` for why that distinction is
   not cosmetic.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from {{ package_name }}.migration import Migration, MigrationError
from {{ package_name }}.store import Applied, Store


class DriftError(MigrationError):
    """An applied migration file no longer matches the ledger."""


class OutOfOrderError(MigrationError):
    """A pending migration is older than one already applied."""


class MigrationFailed(MigrationError):
    """A migration's SQL failed, and its transaction was rolled back."""


@dataclass(frozen=True)
class Step:
    """One migration and what the ledger says about it."""

    migration: Migration
    state: str  # "applied" | "pending" | "drifted"

    @property
    def label(self) -> str:
        """The filename without the extension."""
        return self.migration.label


@dataclass(frozen=True)
class Status:
    """The whole directory, compared against the whole ledger."""

    steps: list[Step]
    applied: dict[str, Applied]

    @property
    def pending(self) -> list[Migration]:
        """Migrations the database has not run yet, in order."""
        return [step.migration for step in self.steps if step.state == "pending"]

    @property
    def drifted(self) -> list[Migration]:
        """Migrations whose file changed after they were applied."""
        return [step.migration for step in self.steps if step.state == "drifted"]

    @property
    def last_applied(self) -> Migration | None:
        """The newest migration in the ledger, whether or not its file is present."""
        present = {
            migration.migration_id: migration
            for migration in (step.migration for step in self.steps)
            if migration.migration_id in self.applied
        }
        if not present:
            return None
        return max(present.values(), key=lambda migration: migration.number)

    def counts(self) -> dict[str, int]:
        """How many migrations are in each state."""
        counts = {"applied": 0, "pending": 0, "drifted": 0}
        for step in self.steps:
            counts[step.state] += 1
        return counts


def plan(migrations: list[Migration], applied: dict[str, Applied]) -> Status:
    """Compare the directory with the ledger. Reads nothing but the two inputs."""
    steps: list[Step] = []
    for migration in migrations:
        record = applied.get(migration.migration_id)
        if record is None:
            state = "pending"
        elif record.checksum != migration.checksum:
            state = "drifted"
        else:
            state = "applied"
        steps.append(Step(migration=migration, state=state))
    return Status(steps=steps, applied=applied)


def split_statements(sql: str) -> list[str]:
    """Split a script into single statements, using SQLite's own parser.

    Splitting on ``;`` is wrong, and the failure is silent until it is not: a
    semicolon inside a string literal (``'it; has one'``), inside a ``BEGIN …
    END`` trigger body, or inside a comment is not a statement boundary. SQLite
    ships the answer in ``sqlite3.complete_statement``, which asks its parser
    whether the buffer it has seen so far is a complete statement; feeding it one
    line at a time is the only splitter that knows the grammar.

    An unterminated statement is an error rather than something to run anyway: the
    file was cut off by an editor or a bad merge, and half a migration applied is
    worse than none.
    """
    statements: list[str] = []
    buffer = ""
    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            if buffer.strip():
                statements.append(buffer.strip())
            buffer = ""
    if buffer.strip() and not _only_comments(buffer):
        raise MigrationError(f"unterminated statement at the end: {buffer.strip()[:60]!r}")
    return statements


def _only_comments(text: str) -> bool:
    """True when the leftover is whitespace and `--` comments, which run nothing.

    `sqlite3.complete_statement` answers False for a buffer holding only a comment,
    so a file that ends in a comment would otherwise look truncated. Line comments
    are the only form this accepts: a dangling `/*` is a broken file, not a tidy one.
    """
    return all(not line.strip() or line.strip().startswith("--") for line in text.splitlines())


def _timestamp(now: Callable[[], datetime]) -> str:
    return now().astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def apply(
    store: Store,
    status: Status,
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> list[Migration]:
    """Run every pending migration, newest last, and return the ones that ran."""
    if status.drifted:
        names = ", ".join(migration.label for migration in status.drifted)
        raise DriftError(f"modified after being applied: {names}")
    newest = status.last_applied
    if newest is not None and status.pending:
        early = [migration for migration in status.pending if migration.number < newest.number]
        if early:
            names = ", ".join(migration.label for migration in early)
            raise OutOfOrderError(
                f"{names} is pending but {newest.label} is already applied; "
                "renumber it above the applied migrations or rebuild the database"
            )

    ran: list[Migration] = []
    for migration in status.pending:
        statements = split_statements(migration.sql)
        if not statements:
            raise MigrationError(f"{migration.path.name}: no statements to run")
        store.connection.execute("BEGIN")
        try:
            for statement in statements:
                store.connection.execute(statement)
            store.record(migration, _timestamp(now))
            store.connection.execute("COMMIT")
        except sqlite3.Error as exc:
            store.connection.execute("ROLLBACK")
            detail = f"{migration.label}: {exc}; nothing from this file was applied"
            raise MigrationFailed(detail) from exc
        ran.append(migration)
    return ran
