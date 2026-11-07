from __future__ import annotations

from {{ package_name }}.automaton import (
    AutomatonError,
    KmpAutomaton,
    failure_table,
    scan_starts,
)
from {{ package_name }}.naive import (
    border_length,
    naive_starts,
)

PATTERNS = ("a", "ab", "aa", "ana", "abra", "anana", "abab", "banana", "aabaaa")
TEXTS = ("", "a", "abracadabra", "bananabanaban", "aaaaaaaaaa")


def test_the_table_is_the_border_count_state_by_state() -> None:
    for pattern in PATTERNS:
        table = failure_table(pattern)
        honest = tuple(
            border_length(pattern[:state]) for state in range(len(pattern) + 1)
        )
        assert table == honest, pattern


def test_the_empty_pattern_owns_one_link() -> None:
    assert failure_table("") == (0,)


def test_the_starts_are_the_naive_starts() -> None:
    for text in TEXTS:
        for pattern in PATTERNS:
            assert scan_starts(text, pattern) == naive_starts(text, pattern)


def test_the_scan_reseats_on_the_failure_link_after_a_hit() -> None:
    assert scan_starts("aabaaabaaa", "aabaaa") == [0, 4]
    assert scan_starts("abababab", "abab") == [0, 2, 4]
    assert scan_starts("aabaaabaaa", "aabaaa") == naive_starts("aabaaabaaa", "aabaaa")


def test_overlaps_start_separately() -> None:
    automaton = KmpAutomaton("ana")
    assert automaton.find_all("banana") == [1, 3]
    assert automaton.find_first("banana") == 1
    assert automaton.count("banana") == 2


def test_an_absent_pattern_answers_quietly() -> None:
    automaton = KmpAutomaton("cadabra")
    assert automaton.find_all("abra") == []
    assert automaton.find_first("abra") is None
    assert automaton.count("abra") == 0


def test_the_empty_pattern_sits_at_every_position() -> None:
    automaton = KmpAutomaton("")
    assert automaton.count("abra") == 5
    assert automaton.find_first("abra") == 0
    assert automaton.find_all("") == [0]


def test_the_audit_is_silent_for_every_shipped_pattern() -> None:
    for pattern in PATTERNS:
        assert KmpAutomaton(pattern).audit() == []


def test_the_pattern_is_kept_and_len_honoured() -> None:
    automaton = KmpAutomaton("anana")
    assert automaton.pattern == "anana"
    assert len(automaton) == 5


def test_a_loud_string_is_refused() -> None:
    try:
        failure_table("Abra")
    except AutomatonError:
        pass
    else:
        raise AssertionError("an uppercase pattern slipped through")
    try:
        scan_starts("ABRA", "a")
    except AutomatonError:
        return
    raise AssertionError("an uppercase text slipped through")
