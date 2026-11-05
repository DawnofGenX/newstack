from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def _write(tmp_path: Path) -> Path:
    path = tmp_path / "samples.jsonl"
    rows = [{"at_us": at * 1_000_000, "value": value} for at, value in
            [(0, 0), (10, 100), (20, 200), (30, 300)]]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def test_a_clean_rollup_prints_rows_and_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = subject.main(["rollup", "--file", str(_write(tmp_path)), "--width", "10"])
    out = capsys.readouterr().out
    assert status == subject.EXIT_OK
    assert "name         shard" in out
    assert "rate     10.000/s" in out
    assert "windows  3 with readings, 0 without" in out


def test_a_missing_window_makes_the_command_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "holed.jsonl"
    rows = [{"at_us": at * 1_000_000, "value": value} for at, value in
            [(0, 0), (10, 10), (30, 30)]]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    status = subject.main(["rollup", "--file", str(path), "--width", "10"])
    out = capsys.readouterr().out
    assert status == subject.EXIT_PROBLEM
    assert "gap      window 20000000..30000000 has no reading" in out


def test_json_output_carries_the_gaps_and_the_rate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = subject.main(["rollup", "--file", str(_write(tmp_path)), "--width", "10", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert status == subject.EXIT_OK
    assert payload["width_us"] == 10_000_000
    assert payload["gaps"] == []
    assert payload["rate_per_second"] == 10.0


def test_merge_reads_two_files_and_reports_the_repeat(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    subject.main(["rollup", "--file", str(_write(tmp_path)), "--width", "10", "--json"])
    payload = capsys.readouterr().out
    first.write_text(payload, encoding="utf-8")
    second.write_text(payload, encoding="utf-8")
    status = subject.main(["merge", str(first), str(second)])
    out = capsys.readouterr().out
    assert status == subject.EXIT_OK
    assert "merged   3 window(s), 3 repeat(s) dropped" in out
    assert "combined across shards" in out


def test_a_missing_file_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status = subject.main(["rollup", "--file", str(tmp_path / "nope.jsonl")])
    assert status == subject.EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_an_empty_file_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("\n", encoding="utf-8")
    assert subject.main(["rollup", "--file", str(path)]) == subject.EXIT_UNUSABLE
    assert "holds no readings" in capsys.readouterr().err


def test_demo_and_selftest_pass(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["demo"]) == subject.EXIT_OK
    assert "0 not as advertised" in capsys.readouterr().out
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
