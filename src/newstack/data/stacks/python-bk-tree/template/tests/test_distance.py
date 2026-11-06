from __future__ import annotations

import pytest

from {{ package_name }}.distance import (
    DistanceError,
    levenshtein,
    osa,
    triangle_violation,
)


def test_a_word_is_zero_from_itself() -> None:
    assert levenshtein("hello", "hello") == 0


def test_edits_are_counted_both_ways() -> None:
    for left, right in [("kitten", "sitting"), ("flaw", "lawn"), ("", "abc"), ("a", "")]:
        assert levenshtein(left, right) == levenshtein(right, left)


def test_transposition_costs_one_only_under_osa() -> None:
    assert levenshtein("ab", "ba") == 2
    assert osa("ab", "ba") == 1


def test_a_limit_reports_limit_plus_one_without_the_answer() -> None:
    wide = levenshtein("a" * 60, "b" * 60, limit=2)
    assert wide == 3


def test_a_limit_does_not_lose_an_exact_small_answer() -> None:
    assert levenshtein("kitten", "sitting", limit=5) == 3


def test_a_negative_limit_is_refused() -> None:
    with pytest.raises(DistanceError):
        levenshtein("a", "b", limit=-1)


def test_osa_breaks_the_triangle_inequality() -> None:
    witness = triangle_violation(["ca", "ac", "abc", "ba", "cab", "bca", "ab"])
    assert witness is not None
    assert witness.through < witness.direct


def test_levenshtein_honours_the_inequality_where_osa_does_not() -> None:
    words = ["ca", "ac", "abc"]
    for left in words:
        for middle in words:
            for right in words:
                assert levenshtein(left, right) <= levenshtein(left, middle) + levenshtein(
                    middle, right
                )
