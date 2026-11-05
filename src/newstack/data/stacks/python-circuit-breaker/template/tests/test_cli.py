"""The CLI is the harness: it must print the timeline and refuse nonsense."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject


def test_demo_prints_a_timeline(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    assert "t=" in out
    assert "verdict   recovered" in out


def test_demo_can_print_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo", "--failures", "2", "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["steps"][0]["state"] == "closed"
    assert any(step["allowed"] is False for step in payload["steps"])


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    out = capsys.readouterr().out
    assert "checks passed, 0 failed" in out


def test_a_bad_argument_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo", "--failures", "0"]) == subject.EXIT_UNUSABLE
    assert "failures must be at least 1" in capsys.readouterr().err


def test_a_missing_subcommand_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main([])
    assert caught.value.code == 2


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
