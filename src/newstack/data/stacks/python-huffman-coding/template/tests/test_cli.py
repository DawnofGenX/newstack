from __future__ import annotations

import json

from {{ package_name }}.cli import (
    EXIT_BROKE,
    EXIT_OK,
    EXIT_UNUSABLE,
    main,
)


def test_encode_prices_a_text(capsys) -> None:
    assert main(["encode", "banana"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "letters    6" in out
    assert "bits" in out


def test_decode_reads_the_bits_back(capsys) -> None:
    assert main(["decode", "0101", "aab"]) == EXIT_OK
    assert "text" in capsys.readouterr().out


def test_frequencies_counts_alphabetically(capsys) -> None:
    assert main(["frequencies", "banana", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {"a": 3, "b": 1, "n": 2}


def test_roundtrip_closes_live(capsys) -> None:
    assert main(["roundtrip", "mississippimississippi", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["closed"] is True
    assert payload["breaks"] == []


def test_report_prices_a_corpus(capsys, tmp_path) -> None:
    corpus = tmp_path / "corpus.txt"
    corpus.write_text("banana\nmississippi\n", encoding="utf-8")
    assert main(["report", "--corpus", str(corpus)]) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert all("letters ->" in line for line in lines)


def test_selftest_and_demo_answer_clean(capsys) -> None:
    assert main(["selftest"]) == EXIT_OK
    assert "0 failed" in capsys.readouterr().out
    assert main(["demo"]) == EXIT_OK
    assert "6 of 6 hold" in capsys.readouterr().out


def test_a_loud_text_exits_two(capsys) -> None:
    assert main(["encode", "Banana"]) == EXIT_UNUSABLE
    assert "not a lowercase letter" in capsys.readouterr().err


def test_a_missing_corpus_exits_two(capsys, tmp_path) -> None:
    assert main(["report", "--corpus", str(tmp_path / "missing.txt")]) == EXIT_UNUSABLE
    assert "no such corpus" in capsys.readouterr().err


def test_the_break_exit_is_one() -> None:
    # a broke roundtrip would answer with EXIT_BROKE; the shipped
    # modules never break, so the constant itself is the contract.
    assert EXIT_BROKE == 1
    assert EXIT_OK == 0
    assert EXIT_UNUSABLE == 2
