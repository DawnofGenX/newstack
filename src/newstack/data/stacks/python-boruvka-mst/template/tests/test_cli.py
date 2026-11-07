from __future__ import annotations

import json

from {{ package_name }}.cli import (
    EXIT_BROKE,
    EXIT_OK,
    EXIT_UNUSABLE,
    main,
)
from {{ package_name }}.selftest import (
    run,
)

LATTICE = ["1", "2", "3", "4", "5", "1>2=4", "2>3=1", "1>4=2", "4>3=1", "3>5=3", "4>5=8"]


def test_tree_answers_the_edge_set(capsys) -> None:
    assert main(["tree", "1", "2", "3", "1>2=4", "2>3=1", "1>3=1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "nodes      3" in out
    assert "edges      2" in out
    assert "2-3 at 1" in out


def test_tree_json_answers_the_edges(capsys) -> None:
    assert main(["tree", "--json", *LATTICE]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {"edge": [1, 4], "weight": 2},
        {"edge": [2, 3], "weight": 1},
        {"edge": [3, 4], "weight": 1},
        {"edge": [3, 5], "weight": 3},
    ]


def test_rounds_runs_the_walk(capsys) -> None:
    assert main(["rounds", "1", "2", "3", "1>2=4", "2>3=1", "1>3=1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "rounds" in out


def test_rounds_json_carries_the_edges(capsys) -> None:
    assert main(["rounds", "--json", "1", "2", "3", "1>2=4", "2>3=1", "1>3=1"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)


def test_a_graph_in_pieces_exits_two(capsys) -> None:
    assert main(["tree", "1", "2", "7", "1>2=1"]) == EXIT_UNUSABLE
    assert "graph is in pieces" in capsys.readouterr().err


def test_a_word_is_not_a_graph(capsys) -> None:
    assert main(["tree", "a", "b"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_report_walks_the_fixture(capsys) -> None:
    assert main(["report", "--corpus", "fixtures/graphs.txt"]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) >= 8
    assert "oracle" in lines[0]


def test_a_missing_corpus_exits_two(capsys) -> None:
    assert main(["report", "--corpus", "nowhere.txt"]) == EXIT_UNUSABLE
    assert "no such corpus" in capsys.readouterr().err


def test_demo_tells_six_stories(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_selftest_runs_from_the_cli(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_the_promises_still_answer_quiet() -> None:
    assert run().failed == 0
    assert run().checks > 30
    assert EXIT_BROKE == 1
