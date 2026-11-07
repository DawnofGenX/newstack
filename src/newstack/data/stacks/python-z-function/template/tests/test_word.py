from __future__ import annotations

from {{ package_name }}.word import (
    MAX_WORD,
    WordError,
    describe,
    ensure_pattern,
    ensure_word,
)


def test_a_word_comes_back_itself() -> None:
    assert ensure_word("abra") == "abra"
    assert ensure_word("") == ""


def test_a_pattern_is_a_word_by_another_name() -> None:
    assert ensure_pattern("ana") == "ana"
    assert ensure_pattern("") == ""


def test_the_display_quoted_shows_emptiness() -> None:
    assert describe("") == "''"
    assert describe("ana") == "'ana'"


def test_noise_is_refused_by_name() -> None:
    for candidate in ("Abra", "ab1", "a b", 7, None, ["a"]):
        try:
            ensure_word(candidate)
        except WordError:
            continue
        raise AssertionError(f"{candidate!r} slipped through the gate")


def test_the_ceiling_is_enforced() -> None:
    assert ensure_word("a" * MAX_WORD)
    try:
        ensure_word("a" * (MAX_WORD + 1))
    except WordError:
        return
    raise AssertionError("a word past the ceiling slipped through")
