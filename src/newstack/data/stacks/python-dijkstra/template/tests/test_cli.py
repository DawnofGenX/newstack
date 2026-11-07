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

LATTICE = ["1", "2", "3", "4", "5", "6", "1>2=4", "2>3=1", "1>4=2", "4>3=1", "3>5=3", "4>5=8"]


def test_distances_answers_the_map(capsys) -> None:
    assert main(["distances", "1", "1", "2", "3", "1>2=4", "2>3=3", "1>3=9"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "source     1" in out
    assert "reached    3" in out
    assert "3 at 7" in out


def test_distances_json_answers_the_map(capsys) -> None:
    assert main(["distances", "1", "--json", *LATTICE]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"1": 0, "2": 4, "3": 3, "4": 2, "5": 6}


def test_path_answers_the_route(capsys) -> None:
    assert main(["path", "1", "5", *LATTICE]) == EXIT_OK
    out = capsys.readouterr().out
    assert "route      1>4>3>5" in out
    assert "cost       6" in out


def test_path_json_carries_the_faces(capsys) -> None:
    assert main(["path", "1", "5", "--json", *LATTICE]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"route": [1, 4, 3, 5], "cost": 6}


def test_a_beyond_reach_target_exits_two(capsys) -> None:
    assert main(["path", "1", "6", *LATTICE]) == EXIT_UNUSABLE
    assert "beyond the reach" in capsys.readouterr().err


def test_report_walks_the_fixture(capsys) -> None:
    assert main(["report", "--corpus", "fixtures/graphs.txt"]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) >= 8
    assert "reached" in lines[0]


def test_a_missing_corpus_exits_two(capsys) -> None:
    assert main(["report", "--corpus", "nowhere.txt"]) == EXIT_UNUSABLE
    assert "no such corpus" in capsys.readouterr().err


def test_a_loud_label_exits_two(capsys) -> None:
    assert main(["distances", "1", "a", "b"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_a_float_label_exits_two() -> None:
    assert main(["distances", "1", "1.5"]) == EXIT_UNUSABLE


def test_a_mute_edge_exits_two() -> None:
    assert main(["distances", "1", "1", "2", "1>2"]) == EXIT_UNUSABLE


def test_demo_tells_six_stories(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_selftest_answers_quiet(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_the_broke_exit_is_reachable(capsys) -> None:
    report = run()
    assert report.failed == 0
    assert EXIT_BROKE != EXIT_OK


def test_the_version_exits_zero(capsys) -> None:
    assert main(["--version"]) == EXIT_OK
    assert "0.1.0" in capsys.readouterr().out
