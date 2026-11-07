from __future__ import annotations

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.scan import (
    scan_array,
    scan_count,
    scan_lcp_array,
    scan_lcp_pair,
    scan_lrs,
)


def test_the_scan_sorts_by_slicing() -> None:
    text = "banana"
    assert scan_array(text) == sorted(range(len(text)), key=lambda at: text[at:])
    assert scan_array("") == []
    assert scan_array("a") == [0]


def test_the_scan_counts_every_start() -> None:
    assert scan_count("aaaa", "aa") == 3
    assert scan_count("banana", "na") == 2
    assert scan_count("banana", "zz") == 0
    assert scan_count("banana", "") == 0


def test_the_scan_pairs_letters_one_by_one() -> None:
    text = "banana"
    assert scan_lcp_pair(text, 1, 3) == 3
    assert scan_lcp_pair(text, 0, 5) == 0
    assert scan_lcp_pair(text, 2, 2) == 4


def test_the_scan_shares_the_neighbours_and_the_repeat() -> None:
    text = "banana"
    order = scan_array(text)
    assert scan_lcp_array(text) == [
        scan_lcp_pair(text, order[k], order[k + 1]) for k in range(len(order) - 1)
    ]
    assert scan_lrs(text) == "ana"
    assert scan_lrs("abc") == ""
    assert scan_lrs("") == ""
    assert scan_lrs("a") == ""
    for seed in (5, 99):
        for body in synthetic(8, seed=seed):
            shares = scan_lcp_array(body)
            tallest = max(shares, default=0)
            if tallest:
                start = scan_array(body)[shares.index(tallest)]
                assert scan_lrs(body) == body[start : start + tallest]
            else:
                assert scan_lrs(body) == ""
