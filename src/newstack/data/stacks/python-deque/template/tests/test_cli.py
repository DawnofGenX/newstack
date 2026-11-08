from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, main


def test_make_runs(capsys) -> None:
    assert main(["make", "1", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "deque" in out


def test_make_json(capsys) -> None:
    assert main(["make", "--json", "1", "2", "3"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == [1, 2, 3]


def test_append_runs(capsys) -> None:
    assert main(["append", "1", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "deque" in out


def test_pop_runs(capsys) -> None:
    assert main(["pop", "1", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "popped" in out


def test_rotate_runs(capsys) -> None:
    assert main(["rotate", "1", "1", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "deque" in out


def test_demo_runs(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "6 of 6 hold" in out


def test_selftest_runs(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "0 failed" in out
