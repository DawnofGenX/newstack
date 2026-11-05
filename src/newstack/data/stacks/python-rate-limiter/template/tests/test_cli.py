"""The CLI is the gate: exit 1 means the limiter said no."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_one_check_is_allowed(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "check", "alice")
    assert status == 0
    assert out.startswith("allow alice")


def test_walking_into_the_limit_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    argv = ("check", "alice", "--limit", "1", "--per", "1", "--capacity", "2", "--repeat", "3")
    status, out, _ = run(capsys, *argv)
    assert status == 1
    assert out.count("allow") == 2
    assert "deny " in out


def test_json_reports_the_wait(capsys: pytest.CaptureFixture[str]) -> None:
    argv = ("check", "alice", "--limit", "1", "--per", "1", "--capacity", "1", "--repeat", "2")
    status, out, _ = run(capsys, *argv, "--json")
    assert status == 1
    payload = json.loads(out)
    assert payload[-1]["allowed"] is False
    assert payload[-1]["retry_after_s"] == 1.0


def test_simulate_counts_the_allowances(capsys: pytest.CaptureFixture[str]) -> None:
    argv = ("simulate", "--limit", "2", "--per", "1", "--capacity", "2", "--requests", "5")
    status, out, _ = run(capsys, *argv)
    assert status == 0
    assert "t=  0.100s" in out
    assert "2 of 5 allowed" in out


def test_demo_prints_a_timeline_and_stats(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "demo")
    assert status == 0
    assert "one too many at once" in out
    assert "stats " in out


def test_a_bad_configuration_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    status, _, err = run(capsys, "check", "alice", "--limit", "0")
    assert status == 2
    assert "limit must be a positive integer" in err


def test_a_bad_cost_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    argv = ("check", "alice", "--limit", "1", "--capacity", "2", "--cost", "5")
    status, _, err = run(capsys, *argv)
    assert status == 2
    assert "exceeds the burst" in err


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "selftest")
    assert status == 0
    assert "0 failed" in out


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
