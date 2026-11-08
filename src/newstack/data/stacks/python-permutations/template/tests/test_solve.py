from __future__ import annotations

import itertools

from {{ package_name }}.solve import (
    PermutationError,
    audit,
    count,
    permutations,
    unique,
)


def test_perm_answers_the_oracle() -> None:
    assert permutations([1, 2, 3]) == list(itertools.permutations([1, 2, 3]))


def test_empty_permutes_empty() -> None:
    assert permutations([]) == [()]


def test_count_is_the_factorial() -> None:
    assert count(4) == 24


def test_unique_dedups() -> None:
    assert len(unique([1, 1, 2])) == 3


def test_audit_stays_silent() -> None:
    assert audit([1, 2, 3]) == []


def test_oversized_is_refused() -> None:
    import pytest

    with pytest.raises(PermutationError):
        permutations(list(range(9)))


def test_non_list_is_refused() -> None:
    import pytest

    with pytest.raises(PermutationError):
        permutations("abc")


def test_count_negative_is_refused() -> None:
    import pytest

    with pytest.raises(PermutationError):
        count(-1)
