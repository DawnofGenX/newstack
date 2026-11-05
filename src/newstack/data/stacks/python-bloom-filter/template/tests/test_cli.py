from pathlib import Path

import pytest

from {{ package_name }}.cli import main


def make(tmp_path: Path, *extra: str) -> Path:
    path = tmp_path / "items.json"
    code = main(["create", "--filter", str(path), "--expected", "100", *extra])
    assert code == 0
    return path


def test_an_item_that_was_added_is_present_and_one_that_was_not_is_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = make(tmp_path)
    assert main(["check", "--filter", str(path), "--item", "alpha"]) == 1
    assert main(["add", "--filter", str(path), "--item", "alpha"]) == 0
    assert main(["check", "--filter", str(path), "--item", "alpha"]) == 0
    assert "maybe: false positives are possible" in capsys.readouterr().out


def test_check_says_absent_definitely(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = make(tmp_path)
    assert main(["check", "--filter", str(path), "--item", "beta"]) == 1
    assert "definite" in capsys.readouterr().out


def test_check_can_answer_in_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = make(tmp_path)
    main(["add", "--filter", str(path), "--item", "alpha"])
    capsys.readouterr()
    assert main(["check", "--filter", str(path), "--item", "alpha", "--json"]) == 0
    assert capsys.readouterr().out.strip() == '{"item": "alpha", "present": true}'


def test_info_reports_a_healthy_filter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = make(tmp_path)
    main(["add", "--filter", str(path), "--item", "alpha"])
    assert main(["info", "--filter", str(path)]) == 0
    out = capsys.readouterr().out
    assert "verdict           healthy" in out
    assert "hashes            7" in out


def test_info_exits_one_when_the_filter_is_saturated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "tiny.json"
    assert main(["create", "--filter", str(path), "--expected", "1"]) == 0
    for number in range(200):
        main(["add", "--filter", str(path), "--item", f"item-{number}"])
    capsys.readouterr()
    assert main(["info", "--filter", str(path)]) == 1
    assert "saturated" in capsys.readouterr().out


def test_creating_twice_needs_force(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = make(tmp_path)
    assert main(["create", "--filter", str(path), "--expected", "10"]) == 2
    assert "--force" in capsys.readouterr().err
    assert main(["create", "--filter", str(path), "--expected", "10", "--force"]) == 0


def test_a_missing_filter_names_the_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "nope.json"
    assert main(["check", "--filter", str(missing), "--item", "alpha"]) == 2
    assert "create one with" in capsys.readouterr().err


def test_a_bad_rate_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.json"
    assert main(["create", "--filter", str(path), "--expected", "10", "--rate", "0"]) == 2
    assert "between 0 and 1" in capsys.readouterr().err


def test_sized_prints_the_budget(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sized", "--expected", "1000", "--rate", "0.01"]) == 0
    out = capsys.readouterr().out
    assert "bits        9586 (9.59 per item)" in out
    capsys.readouterr()
    assert main(["sized", "--expected", "1000", "--json"]) == 0
    assert '"m_bits": 9586' in capsys.readouterr().out


def test_demo_runs_and_reports_the_guarantee(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "no false negatives" in out
    assert "removal is where the guarantee dies" in out


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["selftest"]) == 0
    assert "checks passed" in capsys.readouterr().out
