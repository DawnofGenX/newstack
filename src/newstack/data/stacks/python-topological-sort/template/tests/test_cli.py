"""The command line: one question per run, exit codes kept honest."""

from __future__ import annotations

import {{ package_name }}.cli as cli


def test_the_version_exits_zero(capsys):
    assert cli.main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_an_order_answers_the_ladder(capsys):
    assert cli.main(["order", "1", "2", "3", "4", "1>2", "1>4", "2>3", "4>3"]) == 0
    assert capsys.readouterr().out.strip() == "1>2>4>3"


def test_a_check_holds_and_breaks(capsys):
    assert cli.main(["check", "1>2>3", "1", "2", "3", "1>2", "2>3"]) == 0
    assert "holds" in capsys.readouterr().out
    assert cli.main(["check", "2>1>3", "1", "2", "3", "1>2", "2>3"]) == 1
    assert "broken" in capsys.readouterr().out


def test_a_tangle_is_named_and_refuses(capsys):
    assert cli.main(["cycles", "1", "2", "3", "1>2", "2>3", "3>1"]) == 0
    assert "cycle 1>2>3" in capsys.readouterr().out
    assert cli.main(["order", "1", "2", "3", "1>2", "2>3", "3>1"]) == 2


def test_a_word_is_refused(capsys):
    assert cli.main(["order", "a", "b"]) == 2
    assert "no integer label" in capsys.readouterr().err


def test_a_missing_corpus_exits_two():
    assert cli.main(["report", "--corpus", "nowhere.txt"]) == 2
