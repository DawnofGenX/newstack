from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, main


def test_encode_runs(capsys) -> None:
    assert main(["encode", "abc", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "cipher" in out


def test_encode_json(capsys) -> None:
    assert main(["encode", "--json", "abc", "3"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == "def"


def test_decode_runs(capsys) -> None:
    assert main(["decode", "def", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "plain" in out


def test_brute_runs(capsys) -> None:
    assert main(["brute", "abc"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0:" in out


def test_demo_runs(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "6 of 6 hold" in out


def test_selftest_runs(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 failed" in out
