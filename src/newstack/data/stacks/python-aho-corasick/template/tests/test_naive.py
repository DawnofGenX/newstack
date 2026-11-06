"""The reference scanner: obviously right, deliberately slow, honestly counted."""

from __future__ import annotations

import pytest

from {{ package_name }}.naive import naive_sweep


def test_a_single_pattern_hits_where_the_window_matches() -> None:
    report = naive_sweep("ahishers", ["he"])
    assert [(hit.start, hit.end) for hit in report.hits] == [(4, 5)]


def test_the_ledger_counts_every_window_it_reads() -> None:
    report = naive_sweep("abcde", ["ab", "cd"])
    assert report.inspections == 4 + 4


def test_ties_sort_like_a_sweep() -> None:
    report = naive_sweep("aaa", ["aa", "a"])
    assert [(hit.end, hit.start, hit.pattern) for hit in report.hits] == sorted(
        (hit.end, hit.start, hit.pattern) for hit in report.hits
    )


def test_an_empty_pattern_contributes_nothing() -> None:
    assert naive_sweep("abc", [""]).hits == ()


def test_a_pattern_longer_than_the_text_cannot_start() -> None:
    assert naive_sweep("ab", ["abc"]).hits == ()
    assert naive_sweep("ab", ["abc"]).inspections == 0


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_the_ledger_grows_with_patterns_times_positions(seed: int) -> None:
    text = "abab" * seed
    patterns = ["ab", "ba", "aba"]
    report = naive_sweep(text, patterns)
    assert report.inspections == sum(
        len(text) - len(pattern) + 1 for pattern in patterns
    )
