from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_VALUE,
    SortError,
    audit,
    counts,
    rank,
    sort,
)


def test_sort_answers_the_oracle() -> None:
    assert sort((3, 1, 4, 1, 5, 9, 2, 6)) == sorted((3, 1, 4, 1, 5, 9, 2, 6))


def test_empty_sorts_empty() -> None:
    assert sort(()) == []


def test_counts_is_the_histogram() -> None:
    assert counts((1, 2, 2, 3)) == {1: 1, 2: 2, 3: 1}


def test_rank_is_the_prefix() -> None:
    assert rank((1, 2, 2, 3), 2) == 3
    assert rank((1, 2, 2, 3), 0) == 0


def test_audit_stays_silent() -> None:
    assert audit((3, 1, 4, 1, 5)) == []


def test_negative_is_refused() -> None:
    import pytest

    with pytest.raises(SortError):
        sort((1, -1))


def test_oversized_is_refused() -> None:
    import pytest

    with pytest.raises(SortError):
        sort((1, MAX_VALUE + 1))

