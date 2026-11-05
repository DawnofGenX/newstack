"""The CLI's contract is its exit code, so every code is asserted."""

from __future__ import annotations

import pytest

from {{ package_name }} import cli

INIT = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL);\n"


@pytest.fixture
def project(tmp_path):
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "0001_init.sql").write_text(INIT, encoding="utf-8")
    (folder / "0002_pinned.sql").write_text(
        "ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;\n", encoding="utf-8"
    )
    return tmp_path


def run(project, *args: str) -> int:
    return cli.main([*args, "--db", str(project / "app.db"), "--dir", str(project / "migrations")])


def test_status_lists_every_migration_before_anything_runs(project, capsys) -> None:
    assert run(project, "status") == 0
    out = capsys.readouterr().out
    assert "0001" in out
    assert "pending" in out
    assert "2 migrations: 0 applied, 2 pending, 0 drifted" in out


def test_up_applies_and_says_what_it_applied(project, capsys) -> None:
    assert run(project, "up") == 0
    out = capsys.readouterr().out
    assert "applied 0001_init" in out
    assert "applied 0002_pinned" in out
    assert "applied 2 migrations (0 already present)" in out


def test_up_again_applies_nothing(project, capsys) -> None:
    run(project, "up")
    capsys.readouterr()
    assert run(project, "up") == 0
    assert "applied 0 migrations (2 already present)" in capsys.readouterr().out


def test_verify_is_green_when_the_files_match_the_ledger(project, capsys) -> None:
    run(project, "up")
    capsys.readouterr()
    assert run(project, "verify") == 0
    assert "ok 2 migrations match the ledger" in capsys.readouterr().out


def test_verify_reports_drift_with_exit_one(project, capsys) -> None:
    run(project, "up")
    capsys.readouterr()
    path = project / "migrations" / "0001_init.sql"
    path.write_text(INIT + "-- reworded after it ran\n", encoding="utf-8")
    assert run(project, "verify") == 1
    err = capsys.readouterr().err
    assert "drifted 0001_init" in err
    assert "1 migration(s) changed after being applied" in err


def test_status_also_exits_one_when_a_file_drifted(project) -> None:
    run(project, "up")
    (project / "migrations" / "0002_pinned.sql").write_text("-- rewritten\n", encoding="utf-8")
    assert run(project, "status") == 1


def test_up_refuses_to_run_past_drift(project, capsys) -> None:
    run(project, "up")
    capsys.readouterr()
    (project / "migrations" / "0001_init.sql").write_text(INIT + "\n", encoding="utf-8")
    (project / "migrations" / "0003_more.sql").write_text(
        "ALTER TABLE notes ADD COLUMN more INTEGER;\n", encoding="utf-8"
    )
    assert run(project, "up") == 1
    assert "modified after being applied" in capsys.readouterr().err


def test_a_duplicate_number_exits_two(project, capsys) -> None:
    (project / "migrations" / "0002_again.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert run(project, "up") == 2
    assert "0002 is claimed twice" in capsys.readouterr().err


def test_a_bad_filename_exits_two(project, capsys) -> None:
    (project / "migrations" / "oops.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert run(project, "status") == 2
    assert "expected <number>_<lower_snake_case>.sql" in capsys.readouterr().err


def test_a_missing_directory_exits_two(project, capsys) -> None:
    db = str(project / "app.db")
    assert cli.main(["status", "--db", db, "--dir", str(project / "nope")]) == 2
    assert "not a directory" in capsys.readouterr().err


def test_a_failing_migration_exits_two_and_says_it_rolled_back(project, capsys) -> None:
    (project / "migrations" / "0003_broken.sql").write_text(
        "CREATE TABLE broken (x INTEGER);\nINSERT INTO nope VALUES (1);\n", encoding="utf-8"
    )
    assert run(project, "up") == 2
    assert "nothing from this file was applied" in capsys.readouterr().err


def test_the_version_flag_prints_the_version(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--version"])
    assert caught.value.code == 0
    assert "{{ npm_name }}" in capsys.readouterr().out
