from __future__ import annotations

import itertools

from {{ package_name }}.solve import (
    CombinationError,
    audit,
    combinations,
    count,
    unique,
)


def test_comb_answers_the_oracle() -> None:
    got = combinations([1, 2, 3])
    expected = []
    for r in range(4):
        expected.extend(itertools.combinations([1, 2, 3], r))
    assert sorted(got) == sorted(expected)


def test_empty_combines_empty() -> None:
    assert combinations([]) == [()]


def test_count_is_the_power() -> None:
    assert count(4) == 16


def test_unique_dedups() -> None:
    assert len(unique([1, 1, 2])) == len(set(combinations([1, 1, 2])))


def test_audit_stays_silent() -> None:
    assert audit([1, 2, 3]) == []


def test_oversized_is_refused() -> None:
    import pytest

    with pytest.raises(CombinationError):
        combinations(list(range(9)))


def test_non_list_is_refused() -> None:
    import pytest

    with pytest.raises(CombinationError):
        combinations("abc")


def test_count_negative_is_refused() -> None:
    import pytest

    with pytest.raises(CombinationError):
        count(-1)
