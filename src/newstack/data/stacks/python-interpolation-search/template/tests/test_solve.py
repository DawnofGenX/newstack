"""The search, checked against the oracle, the audit, and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    SearchError,
    audit,
    contains,
    lower_bound,
    search,
)


def test_search_finds_index():
    assert search((1, 3, 5, 7, 9), 5) == 2


def test_search_miss_returns_minus_one():
    assert search((1, 3, 5, 7, 9), 4) == -1


def test_search_empty():
    assert search((), 1) == -1


def test_contains_reports():
    assert contains((1, 2, 3), 2) is True
    assert contains((1, 2, 3), 9) is False


def test_lower_bound():
    assert lower_bound((1, 2, 2, 3), 2) == 1
    assert lower_bound((1, 2, 2, 3), 5) == 4


def test_audit_empty_for_clean():
    assert audit((1, 3, 5, 7, 9), (1, 5, 9)) == []


def test_refuses_unsorted():
    with pytest.raises(SearchError):
        search((3, 1, 2), 1)


def test_refuses_non_int_target():
    with pytest.raises(SearchError):
        search((1, 2, 3), "a")


def test_refuses_non_int_value():
    with pytest.raises(SearchError):
        search((1, "a", 3), 1)


def test_long_project_name_still_fits_line_length():
    # the import below must survive the 47-character project name
    from {{ package_name }}.solve import search as s

    assert s((1, 2, 3), 2) == 1
