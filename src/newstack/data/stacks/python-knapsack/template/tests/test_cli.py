from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, main


def test_solve_runs(capsys) -> None:
    assert main(["solve", "2,3,4", "3,4,5", "5"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "value" in out


def test_solve_json(capsys) -> None:
    assert main(["solve", "2,3,4", "3,4,5", "5", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == 7


def test_witness_runs(capsys) -> None:
    assert main(["witness", "2,3,4", "3,4,5", "5"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "witness" in out


def test_demo_runs(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "6 of 6 hold" in out


def test_selftest_runs(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 failed" in out
