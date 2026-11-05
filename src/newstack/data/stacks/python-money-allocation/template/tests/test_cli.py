"""The CLI prints the minor units next to the formatted amount so a reviewer can check both."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_parse_prints_the_minor_units_and_the_format(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "parse", "12.34 USD")
    assert status == 0
    assert "minor     1234" in out
    assert "exponent 2" in out
    assert "12.34 USD" in out


def test_parse_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "parse", "1200 JPY", "--json")
    assert status == 0
    payload = json.loads(out)
    assert payload == {"amount": 1200, "currency": "JPY", "exponent": 0, "formatted": "1,200 JPY"}


def test_parse_honours_a_rounding_mode(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "parse", "12.345 USD", "--round", "half-up")
    assert status == 0
    assert "minor     1235" in out


def test_an_unspecified_rounding_is_an_error_not_a_guess(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status, out, err = run(capsys, "parse", "12.345 USD")
    assert status == 2
    assert out == ""
    assert "more decimal places" in err


def test_alloc_prints_every_share_and_balances(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "alloc", "100.00 USD", "1", "1", "1")
    assert status == 0
    assert "share 0  ratio    1  33.34 USD" in out
    assert "share 1  ratio    1  33.33 USD" in out
    assert "balances    yes" in out
    assert "total       100.00 USD  (wanted 100.00 USD)" in out


def test_alloc_with_a_bad_ratio_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    status, _, err = run(capsys, "alloc", "100.00 USD", "0", "0")
    assert status == 2
    assert "at least one positive" in err or "zero" in err


def test_split_prints_equal_parts(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "split", "0.10 USD", "3")
    assert status == 0
    assert "share 0  0.04 USD" in out
    assert out.count("0.03 USD") == 2


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "selftest")
    assert status == 0
    assert "0 failed" in out


def test_a_missing_command_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main([])
    assert caught.value.code == 2


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
