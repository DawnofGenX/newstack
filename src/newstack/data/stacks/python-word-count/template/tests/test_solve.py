"""The word count, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    WordCountError,
    audit,
    count_words,
    longest_word,
    word_frequencies,
)


def test_count_words_basic():
    assert count_words("a b c") == 3
    assert count_words("") == 0


def test_word_frequencies_basic():
    assert word_frequencies("a a b") == {"a": 2, "b": 1}


def test_longest_word_basic():
    assert longest_word("a bb ccc") == "ccc"


def test_audit_empty_for_clean():
    assert audit(["a b", "x", ""]) == []


def test_refuses_non_str():
    with pytest.raises(WordCountError):
        count_words(5)


def test_refuses_oversized():
    with pytest.raises(WordCountError):
        count_words("a" * 1001)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import count_words as cw

    assert cw("x y") == 2
