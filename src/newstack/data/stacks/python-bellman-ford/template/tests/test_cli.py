from __future__ import annotations

import json

from {{ package_name }}.cli import (
    EXIT_BROKE,
    EXIT_OK,
    EXIT_UNUSABLE,
    main,
)

DIAMOND = ["1", "2", "3", "4", "1>2=4", "2>3=-2", "3>4=3", "1>3=5", "2>4=1"]
CYCLED = ["0", "1", "2", "3", "0>1=-2", "1>2=1", "2>0=0", "2>3=4"]


def test_the_version_exits_zero(capsys) -> None:
    assert main(["--version"]) == EXIT_OK
    assert "0.1.0" in capsys.readouterr().out


def test_help_exits_zero(capsys) -> None:
    assert main(["--help"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "selftest" in out and "distances" in out


def test_distances_answers_a_walk(capsys) -> None:
    assert main(["distances", *DIAMOND, "--source", "1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "nodes      4" in out
    assert "distance   3 2" in out


def test_distances_answers_json(capsys) -> None:
    argv = ["distances", "1", "2", "3", "1>2=-5", "2>3=2", "--source", "1", "--json"]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"1": 0, "2": -5, "3": -3}


def test_an_unreachable_node_answers_unreached(capsys) -> None:
    assert main(["distances", "3", "8", "--source", "3"]) == EXIT_OK
    assert "distance   8 unreached" in capsys.readouterr().out


def test_cycles_names_a_negative_cycle(capsys) -> None:
    assert main(["cycles", *CYCLED, "--source", "0"]) == EXIT_OK
    assert "cycle      [0, 1, 2]" in capsys.readouterr().out


def test_cycles_answers_none_when_settled(capsys) -> None:
    assert main(["cycles", "1", "2", "1>2=-5", "--source", "1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "cycle      none" in out
    assert "settled    True" in out


def test_report_walks_a_corpus(capsys, tmp_path) -> None:
    corpus = tmp_path / "graphs.txt"
    corpus.write_text("1 2 1>2=-3\n# blank below\n\n4 5\n", encoding="utf-8")
    assert main(["report", "--corpus", str(corpus)]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert "settled True" in lines[0]


def test_a_loud_graph_is_refused(capsys) -> None:
    assert main(["distances", "a", "b", "--source", "1"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_a_missing_corpus_is_refused(capsys) -> None:
    assert main(["report", "--corpus", "/no/such/file.txt"]) == EXIT_UNUSABLE


def test_the_selftest_exits_zero(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_the_demo_exits_zero(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_no_command_is_refused() -> None:
    assert main([]) == EXIT_UNUSABLE


def test_broke_and_unusable_are_distinct() -> None:
    assert EXIT_OK == 0 and EXIT_BROKE == 1 and EXIT_UNUSABLE == 2
