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

DIAMOND = ["0>1=3", "1>3=2", "0>2=2", "2>3=3", "0>3=1", "1>2=1"]


def test_flow_answers_the_value(capsys) -> None:
    assert main(["flow", "0", "3", *DIAMOND]) == EXIT_OK
    out = capsys.readouterr().out
    assert "source     0" in out
    assert "sink       3" in out
    assert "flow       6" in out


def test_flow_json_carries_the_value(capsys) -> None:
    assert main(["flow", "0", "3", "--json", *DIAMOND]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"source": 0, "sink": 3, "flow": 6}


def test_map_answers_the_shipped_arcs(capsys) -> None:
    assert main(["map", "0", "3", *DIAMOND]) == EXIT_OK
    out = capsys.readouterr().out
    assert "flow       6" in out
    assert "0->1 ships 3" in out


def test_map_json_carries_the_shipped_arcs(capsys) -> None:
    assert main(["map", "0", "3", "--json", *DIAMOND]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert {"arc": [0, 1], "shipped": 3} in payload
    assert all(record["shipped"] >= 0 for record in payload)


def test_a_word_is_no_network(capsys) -> None:
    assert main(["flow", "0", "3", "a", "b"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_a_two_way_channel_is_refused(capsys) -> None:
    assert main(["flow", "0", "3", "0>1=2", "1>0=2"]) == EXIT_UNUSABLE


def test_ends_that_match_exit_two(capsys) -> None:
    assert main(["flow", "0", "0", "0>1=1"]) == EXIT_UNUSABLE


def test_a_missing_end_exits_two(capsys) -> None:
    assert main(["flow", "9", "3", *DIAMOND]) == EXIT_UNUSABLE


def test_report_walks_the_fixture(capsys) -> None:
    assert main(["report", "--corpus", "fixtures/networks.txt"]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) >= 8
    assert "cut" in lines[0]


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
