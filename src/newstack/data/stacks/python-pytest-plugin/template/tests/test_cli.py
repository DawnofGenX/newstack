"""The CLI is the reader: every makeable mistake has a distinct exit code."""

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }} import model as model_mod


def sample() -> model_mod.Report:
    return model_mod.Report(
        exit_status=1,
        tests=(
            model_mod.TestRecord(
                "tests/test_a.py::test_slow",
                "passed",
                300.0,
                ("ABC-1",),
                {"call": model_mod.Phase("passed", 300.0)},
            ),
            model_mod.TestRecord("tests/test_a.py::test_quick", "failed", 4.0),
        ),
    )


def test_summary_prints_counts_and_the_slowest_first() -> None:
    lines, status = subject.summarize(sample(), top=2)
    assert status == subject.EXIT_OK
    assert lines[0] == "total 2 tests, 1 passed, 1 failed, 0 skipped, 0 error"
    assert "test_slow" in lines[2]
    assert "[ABC-1]" in lines[2]


def test_gate_fails_only_when_a_test_is_over_the_limit() -> None:
    lines, status = subject.summarize(sample(), fail_over_ms=250.0)
    assert status == subject.EXIT_OVER
    assert "gate   over 250 ms: 1 test(s)" in lines

    ok_lines, ok_status = subject.summarize(sample(), fail_over_ms=300.0)
    assert ok_status == subject.EXIT_OK
    assert "gate   no test over 300 ms" in ok_lines


def test_no_gate_means_no_gate_line() -> None:
    lines, status = subject.summarize(sample())
    assert status == subject.EXIT_OK
    assert not any(line.startswith("gate") for line in lines)


def test_json_summary_is_machine_readable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "report.json"
    model_mod.save(path, sample())
    assert subject.main(["summary", str(path), "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"]["failed"] == 1
    assert payload["slowest"][0]["ticket"] == "ABC-1"
    assert payload["over"] is None


def test_an_unreadable_report_is_exit_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = subject.main(["summary", str(tmp_path / "absent.json")])
    assert status == subject.EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_an_empty_report_is_not_a_crash(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "empty.json"
    model_mod.save(path, model_mod.Report(0, ()))
    assert subject.main(["summary", str(path)]) == subject.EXIT_OK
    printed = capsys.readouterr().out
    assert "total 0 tests" in printed
    assert "slowest" not in printed


def test_selftest_command_runs_the_checks(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "checks passed" in capsys.readouterr().out


def test_a_missing_command_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main([])
    assert caught.value.code == subject.EXIT_UNUSABLE
    assert "usage" in capsys.readouterr().err.lower()


def test_version_does_not_need_a_command(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == subject.EXIT_OK
    assert subject.VERSION in capsys.readouterr().out
