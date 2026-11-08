from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    MAX_LEN,
    LongestCommonSubstringError,
    audit,
    solve,
    witness,
)


def test_classic() -> None:
    assert solve("abcde", "xabcy") == 3


def test_none() -> None:
    assert solve("abc", "xyz") == 0


def test_full() -> None:
    assert solve("abc", "abc") == 3


def test_witness_length() -> None:
    assert len(witness("abcde", "xabcy")) == 3


def test_audit_clean() -> None:
    assert audit("abcde", "xabcy") == []


def test_empty_a() -> None:
    with pytest.raises(LongestCommonSubstringError):
        solve("", "abc")


def test_too_long() -> None:
    with pytest.raises(LongestCommonSubstringError):
        solve("a" * (MAX_LEN + 1), "abc")


def test_non_str() -> None:
    with pytest.raises(LongestCommonSubstringError):
        solve(5, "abc")


def test_witness_contained() -> None:
    w = witness("abcde", "xabcy")
    assert w in "abcde" and w in "xabcy"


def test_single_char() -> None:
    assert solve("a", "a") == 1
