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

DIAMOND = ["1", "2", "3", "4", "5", "6", "1>2", "2>3", "3>1", "3>4", "4>5", "5>4", "4>6"]


def test_components_answers_the_partition(capsys) -> None:
    assert main(["components", "1", "2", "3", "1>2", "2>3", "3>1", "3>4"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "nodes      4" in out
    assert "components 2" in out
    assert "component [1, 2, 3]" in out


def test_components_json_answers_rows(capsys) -> None:
    assert main(["components", "--json", *DIAMOND]) == EXIT_OK
    rows = json.loads(capsys.readouterr().out)
    assert rows == [[1, 2, 3], [4, 5], [6]]


def test_condense_answers_the_fold(capsys) -> None:
    assert main(["condense", *DIAMOND]) == EXIT_OK
    out = capsys.readouterr().out
    assert "heads      [1, 4, 6]" in out
    assert "acyclic    True" in out


def test_condense_json_carries_the_faces(capsys) -> None:
    assert main(["condense", "--json", *DIAMOND]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["heads"] == [1, 4, 6]
    assert payload["acyclic"] is True


def test_report_walks_the_fixture(capsys) -> None:
    assert main(["report", "--corpus", "fixtures/graphs.txt"]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) >= 8
    assert "components" in lines[0]


def test_a_missing_corpus_exits_two(capsys) -> None:
    assert main(["report", "--corpus", "nowhere.txt"]) == EXIT_UNUSABLE
    assert "no such corpus" in capsys.readouterr().err


def test_a_loud_label_exits_two(capsys) -> None:
    assert main(["components", "a", "b"]) == EXIT_UNUSABLE
    assert "no integer label" in capsys.readouterr().err


def test_a_float_label_exits_two() -> None:
    assert main(["components", "1.5"]) == EXIT_UNUSABLE


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
