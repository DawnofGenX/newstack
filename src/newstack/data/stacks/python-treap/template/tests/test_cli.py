from __future__ import annotations

import subprocess
import sys

from {{ package_name }}.cli import main

CODEX = "fixtures/keys.txt"


def test_build_prints_the_shape_the_draws_left(capsys) -> None:
    assert main(["build", "--count", "32"]) == 0
    printed = capsys.readouterr().out
    assert "size 32" in printed
    assert "draws" in printed


def test_rank_reads_the_fixture(capsys) -> None:
    assert main(["rank", "--keys", CODEX, "30"]) == 0
    assert "rank 25" in capsys.readouterr().out


def test_select_names_the_pair_at_a_position(capsys) -> None:
    assert main(["select", "--keys", CODEX, "0"]) == 0
    assert "'-379' = 0" in capsys.readouterr().out


def test_a_position_past_the_tree_reports_it(capsys) -> None:
    assert main(["select", "--keys", CODEX, "99"]) == 1
    assert "holds nothing" in capsys.readouterr().out


def test_split_and_join_report_no_leak(capsys) -> None:
    assert main(["split", "--keys", CODEX, "0"]) == 0
    printed = capsys.readouterr().out
    assert "under    24 key(s)" in printed
    assert "over     21 key(s)" in printed
    assert "restores the tree: True" in printed


def test_a_missing_file_is_unusable(capsys) -> None:
    assert main(["build", "--keys", "nowhere.txt"]) == 2
    assert "cannot read" in capsys.readouterr().err


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
