from __future__ import annotations

from {{ package_name }}.naive import (
    lcp_length,
    naive_count,
    naive_occurrences,
    naive_z,
)


def test_the_stepper_counts_shared_letters() -> None:
    assert lcp_length("anana", "abana") == 1
    assert lcp_length("anana", "anana") == 5
    assert lcp_length("aa", "ab") == 1
    assert lcp_length("ab", "ba") == 0
    assert lcp_length("", "abra") == 0
    assert lcp_length("", "") == 0


def test_the_scan_walks_every_position() -> None:
    assert naive_z("anana") == (5, 0, 3, 0, 1)
    assert naive_z("aa") == (2, 1)
    assert naive_z("ab") == (2, 0)
    assert naive_z("a") == (1,)
    assert naive_z("") == ()


def test_the_occurrence_scan_walks_every_start() -> None:
    assert naive_occurrences("banana", "ana") == [1, 3]
    assert naive_occurrences("aaaa", "aa") == [0, 1, 2]
    assert naive_occurrences("abra", "z") == []
    assert naive_occurrences("", "a") == []


def test_the_empty_pattern_begins_everywhere() -> None:
    assert naive_occurrences("abra", "") == [0, 1, 2, 3, 4]
    assert naive_occurrences("", "") == [0]


def test_the_count_is_the_starts_measured() -> None:
    assert naive_count("banana", "ana") == 2
    assert naive_count("abra", "cadabra") == 0
