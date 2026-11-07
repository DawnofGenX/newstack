from __future__ import annotations

from {{ package_name }}.text import (
    LETTERS,
    MAX_TEXT,
    TextError,
    ensure_text,
)


def test_a_quiet_text_comes_back_itself() -> None:
    assert ensure_text("abra") == "abra"
    assert ensure_text("") == ""


def test_the_letter_set_is_the_lowercase_alphabet() -> None:
    assert len(LETTERS) == 26
    assert LETTERS.islower()


def test_loud_strings_are_refused() -> None:
    for noise in ("Abra", "ab1", "a b", "a.b", 7, None):
        try:
            ensure_text(noise)
        except TextError:
            continue
        raise AssertionError(f"{noise!r} passed the gate")


def test_the_ceiling_is_the_documented_one() -> None:
    assert MAX_TEXT == 100_000
    assert len(ensure_text("a" * MAX_TEXT)) == MAX_TEXT
    try:
        ensure_text("a" * (MAX_TEXT + 1))
    except TextError:
        return
    raise AssertionError("a text past the ceiling passed")
