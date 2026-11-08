from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_LENGTH,
    BracketError,
    count_unmatched,
    is_valid,
    matched_pairs,
)


def test_valid_empty() -> None:
    assert is_valid("") is True


def test_valid_nested() -> None:
    assert is_valid("([])") is True


def test_invalid_mismatch() -> None:
    assert is_valid("([)]") is False


def test_matched_pairs() -> None:
    assert matched_pairs("([])") == [(1, 2), (0, 3)]


def test_count_unmatched() -> None:
    assert count_unmatched("(((") == 3


def test_oversized_refused() -> None:
    import pytest

    with pytest.raises(BracketError):
        is_valid("(" * (MAX_LENGTH + 1))


def test_bad_char_refused() -> None:
    import pytest

    with pytest.raises(BracketError):
        is_valid("(a)")
