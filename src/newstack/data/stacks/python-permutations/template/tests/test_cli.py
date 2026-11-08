from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, EXIT_UNUSABLE, main


def test_perm_runs(capsys) -> None:
    assert main(["perm", "1", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "perms" in out


def test_perm_json(capsys) -> None:
    assert main(["perm", "--json", "1", "2"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == [['1', '2'], ['2', '1']]


def test_count_runs(capsys) -> None:
    assert main(["count", "4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "count" in out


def test_unique_runs(capsys) -> None:
    assert main(["unique", "1", "1", "2"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "unique" in out


def test_oversized_exits_two(capsys) -> None:
    assert main(["perm", "1", "2", "3", "4", "5", "6", "7", "8", "9"]) == EXIT_UNUSABLE
