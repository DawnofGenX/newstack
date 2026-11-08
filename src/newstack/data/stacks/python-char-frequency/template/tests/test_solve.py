"""The character frequency, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    CharFrequencyError,
    audit,
    char_frequencies,
    count_chars,
    most_common,
)


def test_count_chars_basic():
    assert count_chars("a b") == 3
    assert count_chars("") == 0


def test_char_frequencies_basic():
    assert char_frequencies("aab") == {"a": 2, "b": 1}


def test_most_common_basic():
    assert most_common("aab") == "a"


def test_audit_empty_for_clean():
    assert audit(["a b", "x", ""]) == []


def test_refuses_non_str():
    with pytest.raises(CharFrequencyError):
        count_chars(5)


def test_refuses_oversized():
    with pytest.raises(CharFrequencyError):
        count_chars("a" * 1001)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import count_chars as cc

    assert cc("xy") == 2
