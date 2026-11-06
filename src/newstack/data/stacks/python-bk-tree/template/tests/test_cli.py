from __future__ import annotations

import json

import pytest

from {{ package_name }}.cli import EXIT_NONE, EXIT_OK, EXIT_UNUSABLE, main


@pytest.fixture()
def words(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("hello\nhallo\nhelp\nhelm\nzzz\n", encoding="utf-8")
    return str(path)


def test_the_version_names_the_program(capsys) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["--version"])
    assert exit_.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_distance_reports_both_flavours(capsys) -> None:
    assert main(["distance", "ab", "ba"]) == EXIT_OK
    report = capsys.readouterr().out
    assert "edits      2" in report
    assert "with osa   1" in report


def test_search_exits_zero_when_it_finds(capsys, words) -> None:
    assert main(["search", "--words", words, "--word", "hello", "--distance", "1"]) == EXIT_OK
    assert "hallo" in capsys.readouterr().out


def test_search_exits_one_when_it_finds_nothing(capsys, words) -> None:
    assert main(["search", "--words", words, "--word", "xxxx", "--distance", "1"]) == EXIT_NONE
    assert "nothing within that distance" in capsys.readouterr().out


def test_search_json_is_only_json(capsys, words) -> None:
    code = main(["search", "--words", words, "--word", "help", "--distance", "1", "--json"])
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "help"
    assert {"word": "help", "distance": 0} in payload["hits"]


def test_transpositions_turn_the_walk_into_a_scan(capsys, words) -> None:
    code = main(
        [
            "search", "--words", words, "--word", "hello",
            "--distance", "1", "--json", "--transpositions",
        ]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["full_scan"] is True


def test_a_missing_word_list_is_unusable(capsys) -> None:
    code = main(["search", "--words", "nowhere.txt", "--word", "a", "--distance", "1"])
    assert code == EXIT_UNUSABLE
    assert "no such word list" in capsys.readouterr().err


def test_nearest_always_answers(capsys, words) -> None:
    assert main(["nearest", "--words", words, "--word", "hallo"]) == EXIT_OK
    assert "closest    0" in capsys.readouterr().out


def test_tree_reports_the_shape(capsys, words) -> None:
    assert main(["tree", "--words", words]) == EXIT_OK
    assert "same set   True" in capsys.readouterr().out


def test_the_stories_and_the_invariants_hold(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
