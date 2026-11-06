from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from {{ package_name }}.cli import (
    EXIT_NONE,
    EXIT_OK,
    EXIT_UNUSABLE,
    main,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "keys.txt"


def test_the_package_runs_as_a_module() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "{{ package_name }}", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert "0.1.0" in done.stdout


def test_build_prints_the_ledger(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["build", "--count", "32"]) == EXIT_OK
    ledger = capsys.readouterr().out
    assert "size 32" in ledger
    assert "alpha 0.7" in ledger
    assert "balanced 1" in ledger


def test_a_single_key_is_one_key(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["build", "--count", "1"]) == EXIT_OK
    assert "size 1 depth 1" in capsys.readouterr().out


def test_rank_answers_for_every_probe(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["rank", "--keys", str(FIXTURE), "30", "500"]) == EXIT_OK
    answers = capsys.readouterr().out
    assert "rank 20" in answers
    assert "rank 45" in answers


def test_select_lands_and_refuses(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["select", "--keys", str(FIXTURE), "0"]) == EXIT_OK
    assert "-498" in capsys.readouterr().out
    assert main(["select", "--keys", str(FIXTURE), "99"]) == EXIT_NONE
    assert "holds nothing" in capsys.readouterr().out


def test_a_missing_stream_is_unusable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["build", "--keys", "nowhere.txt"]) == EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_a_ruleless_alpha_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["build", "--count", "8", "--alpha", "1.5"]) == EXIT_UNUSABLE
    assert "unit interval" in capsys.readouterr().err


def test_the_storm_reports_what_it_broke(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["storm"]) == EXIT_OK
    assert "0 break(s)" in capsys.readouterr().out


def test_the_stories_all_hold(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_the_invariants_run_from_the_command_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
