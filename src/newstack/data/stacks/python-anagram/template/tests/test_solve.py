"""The anagram, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    AnagramError,
    audit,
    is_anagram,
    signature,
)


def test_is_anagram_basic():
    assert is_anagram("listen", "silent") is True
    assert is_anagram("abc", "def") is False


def test_signature_basic():
    assert signature("abc") == ["a", "b", "c"]


def test_audit_empty_for_clean():
    assert audit([("listen", "silent"), ("abc", "def")]) == []


def test_refuses_non_str():
    with pytest.raises(AnagramError):
        is_anagram(5, "a")


def test_refuses_oversized():
    with pytest.raises(AnagramError):
        is_anagram("a" * 100, "a")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import is_anagram as ia

    assert ia("ab", "ba") is True
