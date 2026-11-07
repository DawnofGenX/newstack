from __future__ import annotations

import pytest

from {{ package_name }}.text import (
    MAX_LENGTH,
    TextError,
    describe,
    ensure_pattern,
    ensure_text,
)


def test_a_text_comes_back_itself() -> None:
    assert ensure_text("banana") == "banana"
    assert ensure_text("") == ""
    assert ensure_text("a" * MAX_LENGTH) == "a" * MAX_LENGTH
    assert describe("banana") == "'banana'"


def test_a_pattern_comes_back_itself() -> None:
    assert ensure_pattern("nan") == "nan"
    assert ensure_pattern("a") == "a"


def test_the_empty_pattern_is_no_pattern() -> None:
    with pytest.raises(TextError, match="empty"):
        ensure_pattern("")


def test_uppercase_has_no_place() -> None:
    with pytest.raises(TextError, match="lowercase"):
        ensure_text("Banana")
    with pytest.raises(TextError, match="lowercase"):
        ensure_pattern("Nan")


def test_a_digit_or_mark_has_no_place() -> None:
    with pytest.raises(TextError, match="non-letter"):
        ensure_text("ban3na")
    with pytest.raises(TextError, match="non-letter"):
        ensure_pattern("na!")


def test_noise_is_refused_by_name() -> None:
    with pytest.raises(TextError, match="not text"):
        ensure_text(["banana"])
    with pytest.raises(TextError, match="not text"):
        ensure_pattern(7)


def test_a_text_past_the_gate_is_refused() -> None:
    with pytest.raises(TextError, match=str(MAX_LENGTH)):
        ensure_text("a" * (MAX_LENGTH + 1))
    with pytest.raises(TextError, match=str(MAX_LENGTH)):
        ensure_pattern("a" * (MAX_LENGTH + 1))
