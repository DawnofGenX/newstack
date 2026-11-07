from __future__ import annotations

from {{ package_name }}.hashing import window_hash
from {{ package_name }}.naive import (
    naive_starts,
)
from {{ package_name }}.scanner import (
    RollingScanner,
    ScannerError,
    scan_starts,
)

PATTERNS = ("a", "ab", "aa", "ana", "abra", "anana", "abab", "banana", "aabaaa")
TEXTS = ("", "a", "abracadabra", "bananabanaban", "aaaaaaaaaa")


def test_the_starts_are_the_naive_starts() -> None:
    for text in TEXTS:
        for pattern in PATTERNS:
            assert scan_starts(text, pattern) == naive_starts(text, pattern)


def test_the_roll_lands_where_the_weigh_lands() -> None:
    scanner = RollingScanner("abra")
    for text in TEXTS:
        assert scanner.audit(text) == []


def test_the_scan_seats_overlapping_starts_in_order() -> None:
    assert scan_starts("aabaaabaaa", "aabaaa") == [0, 4]
    assert scan_starts("abababab", "abab") == [0, 2, 4]
    assert scan_starts("aabaaabaaa", "aabaaa") == naive_starts("aabaaabaaa", "aabaaa")


def test_overlaps_start_separately() -> None:
    scanner = RollingScanner("ana")
    assert scanner.find_all("banana") == [1, 3]
    assert scanner.find_first("banana") == 1
    assert scanner.count("banana") == 2


def test_an_absent_pattern_answers_quietly() -> None:
    scanner = RollingScanner("cadabra")
    assert scanner.find_all("abra") == []
    assert scanner.find_first("abra") is None
    assert scanner.count("abra") == 0


def test_the_empty_pattern_sits_at_every_position() -> None:
    scanner = RollingScanner("")
    assert scanner.count("abra") == 5
    assert scanner.find_first("abra") == 0
    assert scanner.find_all("") == [0]


def test_the_digest_is_the_documented_weigh() -> None:
    scanner = RollingScanner("abra")
    assert scanner.digest == window_hash("abra")
    assert RollingScanner("").digest == 0


def test_collisions_are_tax_never_lies() -> None:
    scanner = RollingScanner("abra")
    tax = scanner.collisions("abracadabra" * 4)
    assert tax >= 0
    assert scanner.find_all("abracadabra" * 4) == naive_starts("abracadabra" * 4, "abra")


def test_the_audit_is_silent_for_every_shipped_pair() -> None:
    for pattern in PATTERNS:
        for text in TEXTS:
            assert RollingScanner(pattern).audit(text) == []


def test_the_pattern_is_kept_and_len_honoured() -> None:
    scanner = RollingScanner("anana")
    assert scanner.pattern == "anana"
    assert len(scanner) == 5


def test_a_loud_string_is_refused() -> None:
    try:
        RollingScanner("Abra")
    except ScannerError:
        pass
    else:
        raise AssertionError("an uppercase pattern slipped through")
    try:
        scan_starts("ABRA", "a")
    except ScannerError:
        return
    raise AssertionError("an uppercase text slipped through")
