from __future__ import annotations

import json

from {{ package_name }}.cli import EXIT_OK, EXIT_UNUSABLE, main


def test_sort_runs(capsys) -> None:
    assert main(["sort", "3", "1", "4", "1", "5"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "sorted" in out


def test_sort_json(capsys) -> None:
    assert main(["sort", "--json", "3", "1", "4"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == [1, 3, 4]


def test_counts_runs(capsys) -> None:
    assert main(["counts", "1", "2", "2", "3"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "values" in out


def test_rank_runs(capsys) -> None:
    assert main(["rank", "1", "2", "2", "3", "2"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "rank" in out


def test_negative_exits_two(capsys) -> None:
    assert main(["sort", "1", "-1"]) == EXIT_UNUSABLE
