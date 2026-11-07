from __future__ import annotations

from {{ package_name }}.text import (
    MAX_TEXT,
    TextError,
    ensure_text,
)


def test_a_text_comes_back_itself() -> None:
    assert ensure_text("abra") == "abra"
    assert ensure_text("") == ""


def test_loud_strings_are_refused() -> None:
    for loud in ("Abra", "ab1", "a b", "a.b", 7, ["a"]):
        try:
            ensure_text(loud)
        except TextError:
            continue
        raise AssertionError(f"{loud!r} passed the gate")


def test_the_ceiling_is_the_documented_one() -> None:
    assert MAX_TEXT == 100_000
    assert ensure_text("a" * 40) == "a" * 40
