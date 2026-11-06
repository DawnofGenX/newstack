from __future__ import annotations

from {{ package_name }}.scan import scan_overlap, scan_stab
from {{ package_name }}.span import Interval

CORPUS = [Interval(0, 4), Interval(2, 6), Interval(6, 10)]


def test_the_scan_finds_every_holder_in_order() -> None:
    assert scan_stab(CORPUS, 3) == [Interval(0, 4), Interval(2, 6)]
    assert scan_stab(CORPUS, 6) == [Interval(6, 10)]
    assert scan_stab(CORPUS, 100) == []


def test_the_scan_touches_every_overlapping_span() -> None:
    assert scan_overlap(CORPUS, 3, 7) == [
        Interval(0, 4),
        Interval(2, 6),
        Interval(6, 10),
    ]
    assert scan_overlap(CORPUS, 4, 6) == [Interval(2, 6)]
    assert scan_overlap(CORPUS, 6, 7) == [Interval(6, 10)]


def test_an_end_touches_nothing_it_ends() -> None:
    assert scan_stab(CORPUS, 6) == [Interval(6, 10)]
    assert scan_overlap(CORPUS, 5, 6) == [Interval(2, 6)]
    assert scan_overlap(CORPUS, 0, 2) == [Interval(0, 4)]
