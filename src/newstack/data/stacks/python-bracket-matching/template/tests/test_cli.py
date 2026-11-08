from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, main


def test_validate_runs(capsys) -> None:
    assert main(["validate", "([])"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "valid" in out


def test_validate_json(capsys) -> None:
    assert main(["validate", "--json", "([])"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload is True


def test_pairs_runs(capsys) -> None:
    assert main(["pairs", "([])"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "pairs" in out


def test_count_runs(capsys) -> None:
    assert main(["count", "((("]) == EXIT_OK
    out = capsys.readouterr().out
    assert "unmatched" in out


def test_demo_runs(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "6 of 6 hold" in out


def test_selftest_runs(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 failed" in out
