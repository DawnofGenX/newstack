"""The sweep and its promises: one pass, every overlap, deterministic order."""

from __future__ import annotations

import pytest

from {{ package_name }}.automaton import AhoCorasick, AhoCorasickError

TEXTBOOK = ("he", "she", "his", "hers")


def machine() -> AhoCorasick:
    return AhoCorasick(TEXTBOOK)


def test_the_textbook_overlaps_all_surface() -> None:
    found = machine().scan("ahishers")
    assert [(hit.pattern, hit.start, hit.end) for hit in found] == [
        ("his", 1, 3),
        ("she", 3, 5),
        ("he", 4, 5),
        ("hers", 4, 7),
    ]


def test_a_shared_prefix_reports_every_embedder() -> None:
    shared = AhoCorasick(["ab", "abc", "bc", "c"])
    assert [hit.pattern for hit in shared.scan("zabcz")] == ["ab", "abc", "bc", "c"]


def test_overlapping_hits_at_one_end_are_sorted() -> None:
    first = AhoCorasick(["aa", "a"]).scan("aaaa")
    assert len(first) == 7
    assert [(hit.end, hit.start, hit.pattern) for hit in first] == sorted(
        (hit.end, hit.start, hit.pattern) for hit in first
    )


def test_a_failure_link_lands_on_the_longest_suffix() -> None:
    built = AhoCorasick(["she"])
    hers = built.root.children["s"].children["h"]
    assert hers.children["e"].fail is built.root


def test_duplicate_patterns_are_stated_once() -> None:
    assert list(AhoCorasick(["ab", "ab", "ab"]).patterns) == ["ab"]
    assert AhoCorasick(["ab"]).count("abab") == 2


def test_an_empty_pattern_set_sweeps_to_nothing() -> None:
    quiet = AhoCorasick([])
    assert quiet.sweep("anything").hits == ()
    assert quiet.states == 1


def test_an_empty_text_sweeps_zero_states() -> None:
    assert AhoCorasick(["he"]).sweep("").states == 0


def test_a_blank_pattern_is_refused() -> None:
    with pytest.raises(AhoCorasickError):
        AhoCorasick([""])


def test_a_non_string_pattern_is_refused() -> None:
    with pytest.raises(AhoCorasickError):
        AhoCorasick([7])  # type: ignore[list-item]


def test_a_non_string_text_is_refused() -> None:
    with pytest.raises(AhoCorasickError):
        machine().sweep(7)  # type: ignore[arg-type]


def test_sweeps_are_repeatable_and_countable() -> None:
    built = machine()
    assert built.scan("shers") == built.scan("shers")
    assert built.count("ahishers") == len(built.scan("ahishers")) == 4


def test_the_ledger_counts_every_state_crossing() -> None:
    sweep = AhoCorasick(["he"]).sweep("he")
    assert sweep.states == 2
    assert sweep.text_length == 2
