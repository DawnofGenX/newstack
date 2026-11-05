from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject


def test_a_burst_collapses_to_one_load(capsys: pytest.CaptureFixture[str]) -> None:
    status = subject.main(["run", "--callers", "20", "--delay", "0.05"])
    out = capsys.readouterr().out
    assert status == subject.EXIT_OK
    assert "1 load(s)" in out
    assert "19 waited" in out
    assert "values   1 distinct" in out


def test_the_json_report_carries_the_stats(capsys: pytest.CaptureFixture[str]) -> None:
    status = subject.main(["run", "--callers", "8", "--delay", "0.02", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == subject.EXIT_OK
    assert payload["stats"]["loads"] == 1
    assert payload["stats"]["waits"] == 7
    assert payload["answers"] == 8


def test_demo_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo"]) == subject.EXIT_OK
    assert "0 not as advertised" in capsys.readouterr().out


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_a_bad_ttl_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    status = subject.main(["run", "--callers", "2", "--delay", "0", "--ttl", "0"])
    assert status == subject.EXIT_UNUSABLE
    assert "ttl must be positive" in capsys.readouterr().err


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
