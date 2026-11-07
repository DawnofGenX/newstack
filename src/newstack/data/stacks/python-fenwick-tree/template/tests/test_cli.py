from __future__ import annotations

import subprocess
import sys

from {{ package_name }}.cli import main

CODEX = "fixtures/values.txt"


def test_build_prints_the_cells_as_they_stand(capsys) -> None:
    assert main(["build", "--count", "32"]) == 0
    printed = capsys.readouterr().out
    assert "size 32" in printed
    assert "walk-limit 6" in printed


def test_sum_answers_the_running_list_sum(capsys) -> None:
    assert main(["sum", "--values", CODEX, "5"]) == 0
    printed = capsys.readouterr().out
    assert "prefix   prefix 5 cells 2 answer 16" in printed


def test_a_count_past_the_tree_is_unusable(capsys) -> None:
    assert main(["sum", "--values", CODEX, "99"]) == 2
    assert "is no count" in capsys.readouterr().out


def test_add_names_the_climb_and_the_new_value(capsys) -> None:
    assert main(["add", "--values", CODEX, "2", "7"]) == 0
    printed = capsys.readouterr().out
    assert "added    add 7 at 2 cells 4 answer 10" in printed


def test_an_index_past_the_tree_is_refused(capsys) -> None:
    assert main(["add", "--values", CODEX, "30", "7"]) == 2
    assert "is no seat" in capsys.readouterr().out


def test_range_answers_the_slice(capsys) -> None:
    assert main(["range", "--values", CODEX, "2", "6"]) == 0
    assert "answer 19" in capsys.readouterr().out


def test_an_inverted_window_is_unusable(capsys) -> None:
    assert main(["range", "--values", CODEX, "6", "2"]) == 2
    assert "unusable" in capsys.readouterr().out


def test_a_missing_value_list_is_unusable(capsys) -> None:
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
