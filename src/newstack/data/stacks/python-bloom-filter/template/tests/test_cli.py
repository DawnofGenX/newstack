"""The command line: one question per run, the exit code keeps the promise."""

from __future__ import annotations

import pytest

from {{ package_name }}.cli import (
    EXIT_MISS,
    EXIT_OK,
    EXIT_UNUSABLE,
    VERSION,
    main,
)


def test_the_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == EXIT_OK
    assert VERSION in capsys.readouterr().out


def test_help_lists_the_questions(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == EXIT_OK
    listed = capsys.readouterr().out
    for command in ("add", "check", "report", "seed", "selftest", "demo"):
        assert command in listed


def test_add_seats_and_the_audit_stays_silent(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "--key", "7", "--key", "42"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "added      7 42" in said
    assert "audit      0 breaks" in said


def test_a_seeded_key_checks_present(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "165"]) == EXIT_OK
    assert "present" in capsys.readouterr().out


def test_an_unseen_key_checks_absent(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", "1"]) == EXIT_MISS
    assert "absent" in capsys.readouterr().out


def test_the_shipped_audit_reports_clean(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["report"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "false neg  0" in said
    assert "false pos  0" in said
    assert "breaks     0" in said


def test_a_seed_replays(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["seed", "7"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "replay     identical" in said
    assert "first keys 165" in said


def test_the_stories_stand(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_the_invariants_hold(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv",
    [
        ["check", "x"],
        ["check", "256"],
        ["check", "-1"],
        ["check", "7", "--width", "7"],
        ["add"],
        ["seed", "-3"],
    ],
)
def test_strangers_leave_the_arguments(argv: list[str]) -> None:
    assert main(argv) == EXIT_UNUSABLE


def test_json_rides_on_the_report(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["report", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["checks"] == 7920
    assert all(not v["false_negatives"] for v in payload["verdicts"])
