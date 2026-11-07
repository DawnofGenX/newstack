from __future__ import annotations

from {{ package_name }}.brute import (
    brute_sort,
    scan_member,
    scan_predecessor,
    scan_successor,
)


def test_the_sort_is_the_builtin_sort() -> None:
    for keys in ([3, 0, 200], [], [7], list(range(255, 0, -7))):
        assert brute_sort(keys) == sorted(keys)


def test_the_scans_answer_on_empty_honest() -> None:
    assert scan_successor([], 0) is None
    assert scan_predecessor([], 255) is None
    assert not scan_member([], 0)


def test_the_scans_answer_at_the_edges() -> None:
    live = [0, 7, 255]
    assert scan_successor(live, 0) == 0
    assert scan_successor(live, 8) == 255
    assert scan_successor(live, 255) == 255
    assert scan_successor(live, 256) is None
    assert scan_predecessor(live, 255) == 255
    assert scan_predecessor(live, 0) == 0
    assert scan_predecessor(live, 6) == 0
    assert scan_member(live, 7)
    assert not scan_member(live, 8)
