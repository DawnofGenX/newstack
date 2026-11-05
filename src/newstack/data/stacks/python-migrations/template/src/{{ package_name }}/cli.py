"""The command line: status, up, verify — and exit codes that mean something.

0 is "the database matches the repository". 1 is "it does not, and only a human
can decide what to do" (drift). 2 is "the request or the directory is unusable"
(bad filename, duplicate id, failing SQL, missing directory). A CI job can gate on
2 without needing to parse prose, and a human can tell a typo from a disagreement.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from {{ package_name }} import __version__
from {{ package_name }}.migration import MigrationError, load
from {{ package_name }}.runner import (
    DriftError,
    MigrationFailed,
    OutOfOrderError,
    Status,
    apply,
    plan,
)
from {{ package_name }}.store import Store

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_UNUSABLE = 2


def _status_of(directory: Path, db: Path) -> tuple[Store, Status]:
    migrations = load(directory)
    store = Store.open(db)
    store.ensure_ledger()
    return store, plan(migrations, store.applied())


def _print_status(status: Status, out) -> None:
    print(f"{'id':<8} {'state':<8} {'checksum':<14} slug", file=out)
    for step in status.steps:
        print(
            f"{step.migration.migration_id:<8} {step.state:<8} {step.migration.short():<14} "
            f"{step.migration.slug}",
            file=out,
        )
    counts = status.counts()
    print(
        f"{len(status.steps)} migrations: {counts['applied']} applied, "
        f"{counts['pending']} pending, {counts['drifted']} drifted",
        file=out,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    parser = argparse.ArgumentParser(
        prog="{{ npm_name }}",
        description="Forward-only SQL migrations for SQLite, with a checksum ledger.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default="app.db", type=Path, help="database (default: app.db)")
    common.add_argument(
        "--dir",
        default=Path("migrations"),
        type=Path,
        help="migration directory (default: migrations)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", parents=[common], help="show every migration and its state")
    subparsers.add_parser("up", parents=[common], help="apply pending migrations")
    subparsers.add_parser("verify", parents=[common], help="check the files against the ledger")
    subparsers.add_parser("selftest", help="run the offline assertion suite")

    args = parser.parse_args(argv)
    if args.command == "selftest":
        from {{ package_name }} import selftest

        return selftest.run()

    try:
        store, status = _status_of(args.dir, args.db)
    except (MigrationError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE

    try:
        if args.command == "status":
            _print_status(status, sys.stdout)
            return EXIT_DRIFT if status.drifted else EXIT_OK

        if args.command == "verify":
            if status.drifted:
                for migration in status.drifted:
                    print(f"drifted {migration.label} {migration.short()}", file=sys.stderr)
                print(
                    f"{len(status.drifted)} migration(s) changed after being applied",
                    file=sys.stderr,
                )
                return EXIT_DRIFT
            print(f"ok {len(status.steps)} migrations match the ledger")
            return EXIT_OK

        ran = apply(store, status)
        for migration in ran:
            print(f"applied {migration.label} {migration.short()}")
        print(f"applied {len(ran)} migrations ({len(status.steps) - len(ran)} already present)")
        return EXIT_OK
    except DriftError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_DRIFT
    except (OutOfOrderError, MigrationFailed, MigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    except sqlite3.Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
