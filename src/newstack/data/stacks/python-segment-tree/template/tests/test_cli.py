from __future__ import annotations

import subprocess
import sys

from {{ package_name }}.cli import main

CODEX = "fixtures/values.txt"


def test_build_prints_the_ladder(capsys) -> None:
    assert main(["build", "--count", "32"]) == 0
    printed = capsys.readouterr().out
    assert "size 32" in printed
    assert "invariant True" in printed


def test_query_answers_with_visits(capsys) -> None:
    assert main(["query", "--values", CODEX, "3", "10"]) == 0
    printed = capsys.readouterr().out
    assert "[3, 10) = 11 visits 3 bound 10" in printed


def test_the_full_window_visits_once(capsys) -> None:
    assert main(["query", "--values", CODEX, "0", "30"]) == 0
    assert "= 1855 visits 4 bound 10" in capsys.readouterr().out


def test_the_empty_window_answers_the_identity(capsys) -> None:
    assert main(["query", "--values", CODEX, "4", "4"]) == 0
    assert "= 0 visits 0 bound 10" in capsys.readouterr().out


def test_the_seam_switches_to_the_floor(capsys) -> None:
    assert main(["query", "--mode", "min", "--values", CODEX, "3", "10"]) == 0
    assert "[3, 10) = -5 visits 3 bound 10" in capsys.readouterr().out


def test_a_window_past_the_end_is_reported(capsys) -> None:
    assert main(["query", "--values", CODEX, "0", "31"]) == 1
    assert "not inside" in capsys.readouterr().out


def test_set_lands_and_refolds(capsys) -> None:
    assert main(["set", "--values", CODEX, "4", "40"]) == 0
    assert "set    4 -> 40 root 1900 invariant True" in capsys.readouterr().out


def test_add_slides_and_refolds(capsys) -> None:
    assert main(["add", "--values", CODEX, "9", "-10"]) == 0
    assert "add    9 by -10 -> -7 root 1845 invariant True" in capsys.readouterr().out


def test_an_index_past_the_end_is_reported(capsys) -> None:
    assert main(["set", "--values", CODEX, "30", "1"]) == 1
    assert "outside" in capsys.readouterr().out


def test_a_missing_codex_is_unusable(capsys) -> None:
    assert main(["build", "--values", "nowhere.txt"]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_the_stories_hold_through_the_cli(capsys) -> None:
    assert main(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out


def test_the_selftest_runs_through_the_cli(capsys) -> None:
    assert main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out


def test_the_package_runs_as_a_module() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "{{ package_name }}", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert "0.1.0" in done.stdout
