from __future__ import annotations

import pytest

from {{ package_name }}.corpus import CorpusError, load_keys, synthetic


def test_blanks_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("# a comment\n7\n\n-3\n7\n", encoding="utf-8")
    assert load_keys(path) == [7, -3, 7]


def test_order_of_arrival_is_kept(tmp_path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("9\n1\n5\n", encoding="utf-8")
    assert load_keys(path) == [9, 1, 5]


def test_a_missing_file_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_keys(tmp_path / "gone.txt")


def test_a_directory_is_not_a_key_list(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_keys(tmp_path)


def test_a_file_of_comments_holds_no_keys(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# nothing but a comment\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(path)


def test_a_non_integer_line_is_named(tmp_path) -> None:
    path = tmp_path / "junk.txt"
    path.write_text("seven\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(path)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(50, seed=7) == synthetic(50, seed=7)
    assert synthetic(50, seed=7) != synthetic(50, seed=8)


def test_generated_keys_are_distinct_and_in_span() -> None:
    keys = synthetic(120, seed=3, low=-100, high=100)
    assert len(set(keys)) == 120
    assert all(-100 <= key < 100 for key in keys)


def test_a_corpus_of_zero_is_not_a_corpus() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_an_empty_span_is_refused() -> None:
    with pytest.raises(CorpusError):
        synthetic(4, low=5, high=5)


def test_a_span_too_narrow_for_the_count_is_refused() -> None:
    with pytest.raises(CorpusError):
        synthetic(10, low=0, high=5)
