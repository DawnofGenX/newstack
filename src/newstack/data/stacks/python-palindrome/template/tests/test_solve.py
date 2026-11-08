"""The palindrome, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    PalindromeError,
    audit,
    is_palindrome,
    reverse,
)


def test_is_palindrome_basic():
    assert is_palindrome("aba") is True
    assert is_palindrome("ab") is False


def test_reverse_basic():
    assert reverse("ab") == "ba"


def test_audit_empty_for_clean():
    assert audit(["aba", "ab", "a", ""]) == []


def test_refuses_non_str():
    with pytest.raises(PalindromeError):
        is_palindrome(5)


def test_refuses_oversized():
    with pytest.raises(PalindromeError):
        is_palindrome("a" * 100)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import is_palindrome as ip

    assert ip("aba") is True
