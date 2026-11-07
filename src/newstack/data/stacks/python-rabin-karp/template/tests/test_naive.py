from __future__ import annotations

from {{ package_name }}.naive import (
    naive_count,
    naive_starts,
)


def test_the_scan_walks_every_start() -> None:
    assert naive_starts("banana", "ana") == [1, 3]
    assert naive_starts("aaaa", "aa") == [0, 1, 2]
    assert naive_starts("abra", "z") == []
    assert naive_starts("", "a") == []


def test_the_empty_pattern_begins_everywhere() -> None:
    assert naive_starts("abra", "") == [0, 1, 2, 3, 4]
    assert naive_starts("", "") == [0]


def test_the_count_is_the_starts_measured() -> None:
    assert naive_count("banana", "ana") == 2
    assert naive_count("abra", "cadabra") == 0
