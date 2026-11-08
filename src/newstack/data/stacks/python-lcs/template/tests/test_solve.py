"""The lcs, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import LcsError, audit, lcs, lcs_length


def test_lcs_basic():
    assert lcs("abcde", "ace") == "ace"


def test_length_basic():
    assert lcs_length("abcde", "ace") == 3


def test_empty():
    assert lcs("", "abc") == ""


def test_audit_empty_for_clean():
    assert audit([("abcde", "ace"), ("abc", "abc")]) == []


def test_refuses_non_str():
    with pytest.raises(LcsError):
        lcs(1, "a")


def test_refuses_oversized():
    with pytest.raises(LcsError):
        lcs("a" * 65, "b")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import lcs as L

    assert L("ab", "ab") == "ab"
