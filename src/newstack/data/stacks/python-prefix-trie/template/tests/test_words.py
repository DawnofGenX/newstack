from __future__ import annotations

import pytest

from {{ package_name }}.words import (
    MAX_LENGTH,
    WordError,
    describe,
    ensure_prefix,
    ensure_word,
)


def test_a_word_comes_back_itself() -> None:
    assert ensure_word("cart") == "cart"
    assert ensure_word("a") == "a"
    assert ensure_word("a" * MAX_LENGTH) == "a" * MAX_LENGTH
    assert describe("cart") == "'cart'"


def test_the_empty_string_is_no_word() -> None:
    with pytest.raises(WordError, match="empty"):
        ensure_word("")


def test_strangers_are_refused_by_name() -> None:
    for stranger in ("Cart", "car1", "c-at", "car ", 7, ["cart"], None, True):
        with pytest.raises(WordError):
            ensure_word(stranger)


def test_a_word_past_the_gate_is_refused() -> None:
    with pytest.raises(WordError, match="past"):
        ensure_word("a" * (MAX_LENGTH + 1))


def test_the_stem_gate_opens_for_the_empty_stem() -> None:
    assert ensure_prefix("") == ""
    assert ensure_prefix("car") == "car"
    for stranger in ("Cart", "car1", 7, None):
        with pytest.raises(WordError):
            ensure_prefix(stranger)
