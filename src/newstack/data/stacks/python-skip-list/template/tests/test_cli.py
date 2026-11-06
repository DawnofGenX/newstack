from __future__ import annotations

import pytest

from {{ package_name }}.cli import EXIT_NONE, EXIT_OK, EXIT_UNUSABLE, main


@pytest.fixture()
def pairs(tmp_path):
    path = tmp_path / "pairs.txt"
    path.write_text("1 10\n2 20\n3 30\n4 40\n5 50\n", encoding="utf-8")
    return str(path)


def test_the_version_names_the_program(capsys) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["--version"])
    assert exit_.value.code == 0
    assert "0.1.0" in capsys.readouterr().out


def test_build_prints_the_shape_the_coins_left(capsys) -> None:
    assert main(["build", "--count", "32"]) == EXIT_OK
    report = capsys.readouterr().out
    assert "size 32" in report
    assert "coin flip" in report


def test_build_reads_a_pair_stream(capsys, pairs) -> None:
    assert main(["build", "--pairs", pairs]) == EXIT_OK
    assert "size 5" in capsys.readouterr().out


def test_rank_answers_for_every_key_given(capsys, pairs) -> None:
    assert main(["rank", "--pairs", pairs, "3", "99"]) == EXIT_OK
    report = capsys.readouterr().out
    assert "rank 2" in report
    assert "rank 5" in report


def test_select_names_the_pair_at_a_position(capsys, pairs) -> None:
    assert main(["select", "--pairs", pairs, "0"]) == EXIT_OK
    assert "'1' = 10" in capsys.readouterr().out


def test_a_position_past_the_map_answers_none(capsys, pairs) -> None:
    assert main(["select", "--pairs", pairs, "99"]) == EXIT_NONE
    assert "holds nothing" in capsys.readouterr().out


def test_a_missing_pair_stream_is_unusable(capsys) -> None:
    code = main(["build", "--pairs", "nowhere.txt"])
    assert code == EXIT_UNUSABLE
    assert "cannot read" in capsys.readouterr().err


def test_the_demo_exits_when_every_story_holds(capsys) -> None:
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_the_selftest_exits_when_the_invariants_hold(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
