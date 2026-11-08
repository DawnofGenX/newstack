"""The vowel count, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    VowelCountError,
    audit,
    count_vowels,
    is_vowel,
    vowel_positions,
)


def test_count_vowels_basic():
    assert count_vowels("hello") == 2
    assert count_vowels("") == 0


def test_is_vowel_basic():
    assert is_vowel("a") is True
    assert is_vowel("b") is False


def test_vowel_positions_basic():
    assert vowel_positions("hello") == [1, 4]


def test_audit_empty_for_clean():
    assert audit(["hello", "xyz", "AEIOU"]) == []


def test_refuses_non_str():
    with pytest.raises(VowelCountError):
        count_vowels(5)


def test_refuses_oversized():
    with pytest.raises(VowelCountError):
        count_vowels("a" * 100)


def test_refuses_bad_char():
    with pytest.raises(VowelCountError):
        is_vowel("ab")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import count_vowels as cv

    assert cv("aeiou") == 5
