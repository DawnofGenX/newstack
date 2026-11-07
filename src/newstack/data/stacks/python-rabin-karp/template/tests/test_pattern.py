from __future__ import annotations

from {{ package_name }}.pattern import (
    MAX_PATTERN,
    PatternError,
    describe,
    ensure_pattern,
    ensure_text,
)


def test_a_pattern_comes_back_itself() -> None:
    assert ensure_pattern("abra") == "abra"
    assert ensure_pattern("") == ""


def test_a_text_comes_back_itself() -> None:
    assert ensure_text("banana") == "banana"
    assert ensure_text("") == ""


def test_the_display_quoted_shows_emptiness() -> None:
    assert describe("") == "''"
    assert describe("ana") == "'ana'"


def test_noise_is_refused_by_name() -> None:
    for candidate in ("Abra", "ab1", "a b", 7, None, ["a"]):
        try:
            ensure_pattern(candidate)
        except PatternError:
            continue
        raise AssertionError(f"{candidate!r} slipped through")


def test_the_ceiling_is_enforced() -> None:
    assert ensure_pattern("a" * MAX_PATTERN) == "a" * MAX_PATTERN
    try:
        ensure_pattern("a" * (MAX_PATTERN + 1))
    except PatternError:
        return
    raise AssertionError("an oversized pattern slipped through")
