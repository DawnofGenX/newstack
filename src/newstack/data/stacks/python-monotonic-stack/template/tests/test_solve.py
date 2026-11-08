from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_LEN,
    MonotonicError,
    audit,
    next_greater,
    next_smaller,
    previous_greater,
)


def test_empty_next_greater() -> None:
    assert next_greater([]) == []


def test_lone_value() -> None:
    assert next_greater([7]) == [None]


def test_increasing() -> None:
    assert next_greater([1, 2, 3]) == [2, 3, None]


def test_decreasing() -> None:
    assert next_greater([3, 2, 1]) == [None, None, None]


def test_sample_greater() -> None:
    assert next_greater([2, 1, 3]) == [3, 3, None]


def test_sample_smaller() -> None:
    assert next_smaller([2, 1, 3]) == [1, None, None]


def test_sample_previous() -> None:
    assert previous_greater([2, 1, 3]) == [None, 2, None]


def test_audit_shape() -> None:
    got = audit([2, 1, 3])
    assert got["length"] == 3
    assert got["next_greater_count"] == 2
    assert got["ok"] is True


def test_oversized_refused() -> None:
    import pytest

    with pytest.raises(MonotonicError):
        next_greater(list(range(MAX_LEN + 1)))


def test_non_list_refused() -> None:
    import pytest

    with pytest.raises(MonotonicError):
        next_greater("abc")


def test_oracle_matches_naive() -> None:
    rng_values = [4, 2, 5, 1, 3]
    got = next_greater(rng_values)
    want = []
    for i in range(len(rng_values)):
        found = None
        for j in range(i + 1, len(rng_values)):
            if rng_values[j] > rng_values[i]:
                found = rng_values[j]
                break
        want.append(found)
    assert got == want
