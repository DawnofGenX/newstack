from __future__ import annotations

import json

import pytest

from {{ package_name }}.cli import main

FIXTURE = "fixtures/stream.txt"


def _run(argv: list[str]) -> int:
    return main(argv)


def test_the_version_and_help_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out
    assert _run(["--help"]) == 0


def test_a_counted_key_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["count", "--stream", FIXTURE, "7"]) == 0
    assert "count      1" in capsys.readouterr().out


def test_an_absent_key_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["count", "--stream", FIXTURE, "1"]) == 1
    assert "count      0" in capsys.readouterr().out


def test_the_json_answer_carries_the_cells(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(["count", "--stream", FIXTURE, "--json", "199"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 3
    assert payload["tracked"] is True
    assert len(payload["cells"]) == 5


def test_an_add_grows_the_ledger(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["add", "--stream", FIXTURE, "7", "2"]) == 0
    out = capsys.readouterr().out
    assert "count      3" in out
    assert "total      38" in out


def test_the_report_names_the_shape(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["report", "--stream", FIXTURE]) == 0
    out = capsys.readouterr().out
    assert "width      256" in out
    assert "drift      0" in out


def test_a_seed_replays_itself(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["seed", "--count", "6", "--seed", "7"]) == 0
    first = capsys.readouterr().out
    assert _run(["seed", "--count", "6", "--seed", "7"]) == 0
    assert capsys.readouterr().out == first


def test_a_missing_stream_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["count", "--stream", "nope.txt", "7"]) == 2
    assert "no such stream" in capsys.readouterr().err


def test_an_off_universe_key_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["count", "--stream", FIXTURE, "300"]) == 2
    assert "off [0, 256)" in capsys.readouterr().err


def test_the_selftest_and_demo_pass(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out
    assert _run(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out
