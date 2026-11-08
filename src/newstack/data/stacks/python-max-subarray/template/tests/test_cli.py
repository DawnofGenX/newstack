from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, main


def test_solve_runs(capsys) -> None:
    assert main(["solve", "1,-3,4,-1,2,1,-5,4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "answer" in out


def test_solve_json(capsys) -> None:
    assert main(["solve", "1,-3,4,-1,2,1,-5,4", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == 6


def test_witness_runs(capsys) -> None:
    assert main(["witness", "1,-3,4,-1,2,1,-5,4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "witness" in out


def test_audit_runs(capsys) -> None:
    assert main(["audit", "1,-3,4,-1,2,1,-5,4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "audit: clean" in out


def test_demo_runs(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "ok" in out


def test_selftest_runs(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 failed" in out
