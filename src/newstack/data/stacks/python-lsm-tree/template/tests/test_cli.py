from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }}.cli import main

EXIT_OK = subject.EXIT_OK
EXIT_NONE = subject.EXIT_NONE
EXIT_UNUSABLE = subject.EXIT_UNUSABLE


def test_version_and_help_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == EXIT_OK
    assert "0.1.0" in capsys.readouterr().out
    assert main(["--help"]) == EXIT_OK


def test_put_then_get_answers(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    room = str(tmp_path / "table")
    assert main(["put", "--dir", room, "--key", "12", "--value", "alpha"]) == EXIT_OK
    assert main(["get", "--dir", room, "--key", "12"]) == EXIT_OK
    assert "alpha" in capsys.readouterr().out
    assert main(["get", "--dir", room, "--key", "13"]) == EXIT_NONE


def test_get_json_names_the_answer(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    room = str(tmp_path / "table")
    main(["put", "--dir", room, "--key", "12", "--value", "alpha"])
    capsys.readouterr()
    assert main(["get", "--dir", room, "--key", "12", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["value"] == "alpha"


def test_a_tombstone_answers_absent(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    room = str(tmp_path / "table")
    main(["put", "--dir", room, "--key", "3", "--value", "buried"])
    assert main(["delete", "--dir", room, "--key", "3"]) == EXIT_OK
    assert main(["get", "--dir", room, "--key", "3"]) == EXIT_NONE


def test_a_flush_of_nothing_reports_nothing(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    room = str(tmp_path / "table")
    assert main(["flush", "--dir", room]) == EXIT_NONE


def test_the_workload_agrees_with_the_dict(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    room = str(tmp_path / "table")
    assert main(["workload", "--dir", room, "--seed", "7", "--limit", "3"]) == EXIT_OK
    assert "agreed     True" in capsys.readouterr().out


def test_a_broken_limit_is_unusable(tmp_path) -> None:
    assert main(["workload", "--dir", str(tmp_path / "t"), "--limit", "0"]) == EXIT_UNUSABLE


def test_demo_stories_hold(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "FAIL" not in capsys.readouterr().out


def test_selftest_reports_no_failures(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
