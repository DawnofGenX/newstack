from __future__ import annotations

from {{ package_name }}.array import (
    SEP,
    ArrayError,
    ZArray,
    occurrences,
    z_function,
)
from {{ package_name }}.naive import naive_occurrences, naive_z

WORDS = ("", "a", "aa", "ana", "abra", "anana", "banana", "abracadabra")
PATTERNS = ("a", "ab", "ana", "abra", "anana", "banana")


def test_the_array_is_the_steppers_answer() -> None:
    for word in WORDS:
        assert z_function(word) == naive_z(word)


def test_z_zero_is_the_length_of_the_word() -> None:
    for word in WORDS:
        cut = z_function(word)
        assert cut == () or cut[0] == len(word)
    assert z_function("anana") == (5, 0, 3, 0, 1)


def test_the_array_of_a_loud_word_is_refused() -> None:
    try:
        z_function("Abra")
    except ArrayError:
        return
    raise AssertionError("a loud word cut an array")


def test_the_occurrences_are_the_scan_starts() -> None:
    for word in WORDS:
        for pattern in PATTERNS:
            assert occurrences(word, pattern) == naive_occurrences(word, pattern)


def test_the_separator_is_no_letter() -> None:
    assert SEP.isprintable() is False or SEP == "\x00"
    assert not ("a" <= SEP <= "z")


def test_the_derived_starts_keep_the_overlaps() -> None:
    assert occurrences("banana", "ana") == [1, 3]
    assert occurrences("aaaa", "aa") == [0, 1, 2]
    assert occurrences("banananananas", "anana") == [1, 3, 5, 7]


def test_the_seat_answers_its_questions() -> None:
    seat = ZArray("abracadabra")
    assert seat.word == "abracadabra"
    assert seat.array == z_function("abracadabra")
    assert seat.audit() == []
    assert seat.starts_of("abra") == [0, 7]
    assert seat.first_of("abra") == 0
    assert seat.count_of("abra") == 2
    assert seat.first_of("cadabra") == 4
    assert len(seat) == 11


def test_the_seat_of_the_empty_word_is_honest() -> None:
    seat = ZArray("")
    assert seat.array == ()
    assert seat.audit() == []
    assert seat.starts_of("") == [0]
    assert seat.count_of("a") == 0
    assert seat.first_of("a") is None
