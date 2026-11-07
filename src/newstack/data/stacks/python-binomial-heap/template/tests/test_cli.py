from __future__ import annotations

from {{ package_name }}.cli import main

CODEX = "fixtures/keys.txt"


def test_push_names_the_rank_the_key_reached(capsys) -> None:
    assert main(["push", "30"]) == 0
    printed = capsys.readouterr().out
    assert "pushed       30  push rank 0 linked=False" in printed


def test_push_onto_a_loaded_forest_keeps_the_bits(capsys) -> None:
    assert main(["push", "--keys", CODEX, "7"]) == 0
    printed = capsys.readouterr().out
    assert "push rank" in printed
    assert "bits 101111" in printed


def test_a_word_is_no_key(capsys) -> None:
    assert main(["push", "seven"]) == 2
    assert "is no key" in capsys.readouterr().out


def test_pop_answers_in_order(capsys) -> None:
    assert main(["pop", "--keys", CODEX, "3"]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert "popped   '-120' = 34" in printed[0]
    assert "popped   '-13' = 18" in printed[2]


def test_popping_past_the_forest_reports_it(capsys) -> None:
    assert main(["pop", "--keys", CODEX, "99"]) == 1
    assert "drained  empty" in capsys.readouterr().out


def test_meld_unions_and_empties_the_donor(capsys) -> None:
    assert main(["meld", "1", "2", "3"]) == 0
    printed = capsys.readouterr().out
    assert "melded   64 + 3 into 67" in printed
    assert "donor    0 key(s) left" in printed


def test_a_meld_of_words_is_refused(capsys) -> None:
    assert main(["meld", "--keys", CODEX, "nine"]) == 2


def test_size_walks_the_bit_pattern(capsys) -> None:
    assert main(["size", "--keys", CODEX]) == 0
    printed = capsys.readouterr().out
    assert "size     47, bits 101111, ranks [0, 1, 2, 3, 5]" in printed
    assert "invariant True" in printed


def test_peek_names_the_standing_forest(capsys) -> None:
    assert main(["peek", "--count", "64"]) == 0
    assert "ranks [6]" in capsys.readouterr().out


def test_a_missing_file_is_unusable(capsys) -> None:
    assert main(["size", "--keys", "nowhere.txt"]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_demo_and_selftest_answer(capsys) -> None:
    assert main(["demo"]) == 0
    assert "6 of 6 hold" in capsys.readouterr().out
    assert main(["selftest"]) == 0
    assert "0 failed" in capsys.readouterr().out
