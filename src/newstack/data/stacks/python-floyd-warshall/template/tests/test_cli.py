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


def test_table_answers_the_pairs(capsys) -> None:
    assert main(["table", "1", "2", "3", "1>2=4", "2>3=1", "1>3=9"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "pairs      6" in out
    assert "1->3 at 5" in out


def test_table_json_answers_the_pairs(capsys) -> None:
    assert main(["table", "--json", *LATTICE]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert {"pair": [1, 5], "cost": 6} in payload
    assert all(entry["pair"] != [5, 1] for entry in payload)


def test_worst_answers_the_farthest_hop(capsys) -> None:
    assert main(["worst", "1", "2", "3", "1>2=4", "2>3=1", "1>3=9"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "worst      1->3" in out
    assert "cost       5" in out


def test_worst_json_carries_the_hop(capsys) -> None:
    assert main(["worst", "--json", *LATTICE]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"source": 1, "target": 5, "cost": 6}


def test_a_one_way_table_omits_the_back_road(capsys) -> None:
    assert main(["table", "1", "2", "1>2=7"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "1->2 at 7" in out
    assert "2->1" not in out


def test_a_lone_node_names_no_distance(capsys) -> None:
    assert main(["worst", "4"]) == EXIT_UNUSABLE
    assert "nothing is distant" in capsys.readouterr().err


def test_a_word_is_not_a_graph(capsys) -> None:
    assert main(["table", "a", "b"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_report_walks_the_fixture(capsys) -> None:
    assert main(["report", "--corpus", "fixtures/graphs.txt"]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) >= 8
    assert "walker" in lines[0]


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
