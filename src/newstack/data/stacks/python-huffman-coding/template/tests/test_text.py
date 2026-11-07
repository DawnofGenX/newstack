from __future__ import annotations

from {{ package_name }}.text import (
    LETTERS,
    MAX_TEXT,
    TextError,
    ensure_text,
)


def test_a_text_comes_back_itself() -> None:
    assert ensure_text("abra") == "abra"
    assert ensure_text("") == ""
    assert ensure_text("a" * MAX_TEXT) == "a" * MAX_TEXT


def test_loud_strings_are_refused() -> None:
    for loud in ("Abra", "ab1", "a b", "a.b", 7, ["a"]):
        try:
            ensure_text(loud)
        except TextError:
            continue
        raise AssertionError(f"{loud!r} should not pass the gate")


def test_the_alphabet_is_the_documented_one() -> None:
    assert len(LETTERS) == 26
    assert LETTERS.islower()
    assert all(letter in LETTERS for letter in "huffman")
