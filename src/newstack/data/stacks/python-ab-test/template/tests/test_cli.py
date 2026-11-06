"""The command line: exit codes are the contract."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli


def test_a_comparison_prints_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["compare", "--control", "control=100/1000",
                     "--treatment", "treatment=130/1000"]) == 0
    out = capsys.readouterr().out
    assert "difference" in out
    assert "higher" in out


def test_the_json_form_carries_the_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["compare", "--control", "control=100/1000",
                     "--treatment", "treatment=130/1000", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["z"] == pytest.approx(2.1027, abs=1e-4)
    assert payload["significant"] is True


def test_a_mismatched_split_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main(["srm", "--control", "control=500/102000",
                     "--treatment", "treatment=500/100000"])
    assert code == 1
    assert "MISMATCH" in capsys.readouterr().out


def test_a_plausible_split_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["srm", "--control", "control=500/50100",
                     "--treatment", "treatment=500/50000"]) == 0
    assert "plausible" in capsys.readouterr().out


def test_power_prints_both_directions(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["power", "--baseline", "0.10", "--lift", "0.05",
                     "--visitors", "20000"]) == 0
    out = capsys.readouterr().out
    assert "57,763" in out
    assert "8.56%" in out


def test_peeking_gates_on_its_own_spending(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["peeking", "--trials", "300", "--visitors", "2000",
                     "--looks", "5", "--seed", "5"]) == 0
    assert "boundary held" in capsys.readouterr().out


def test_a_bad_arm_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["compare", "--control", "control=10", "--treatment", "t=1/10"]) == 2
    assert "error" in capsys.readouterr().err


def test_a_bad_probability_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["power", "--baseline", "1.5", "--lift", "0.05"]) == 2
    assert "error" in capsys.readouterr().err


def test_the_version_banner_names_the_program(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--version"])
    assert caught.value.code == 0
    assert "{{ npm_name }} " in capsys.readouterr().out


def test_no_command_is_an_error() -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main([])
    assert caught.value.code == 2
