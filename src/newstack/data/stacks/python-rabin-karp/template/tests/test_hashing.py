from __future__ import annotations

from {{ package_name }}.hashing import (
    BASE,
    MODULUS,
    HashError,
    leading_power,
    letter_value,
    roll,
    window_hash,
    windows,
)

TEXTS = ("", "a", "abracadabra", "bananabanaban", "aaaaaaaaaa", "abcababcabcab")


def test_letters_weigh_one_to_twenty_six() -> None:
    assert letter_value("a") == 1
    assert letter_value("z") == 26
    for candidate in ("A", "1", " ", ""):
        try:
            letter_value(candidate)
        except HashError:
            continue
        raise AssertionError(f"{candidate!r} slipped through")


def test_the_weigh_walks_the_window() -> None:
    assert window_hash("") == 0
    assert window_hash("a") == 1
    assert window_hash("ab") == BASE + 2
    assert window_hash("b") == 2
    assert window_hash("ab") != window_hash("b")


def test_the_base_and_modulus_are_the_documented_ones() -> None:
    assert BASE == 911
    assert MODULUS == 1_000_000_007


def test_the_leading_power_carries_the_outgoing_letter() -> None:
    assert leading_power(1) == 1
    assert leading_power(2) == BASE
    assert leading_power(3) == BASE * BASE % MODULUS
    assert leading_power(0) == 0
    try:
        leading_power(-1)
    except HashError:
        return
    raise AssertionError("a negative width slipped through")


def test_the_roll_equals_the_fresh_weigh_everywhere() -> None:
    for width in (1, 2, 3, 5, 7):
        for text in TEXTS:
            for start, window in enumerate(windows(text, width)):
                if start == 0:
                    continue
                rolled = roll(
                    window_hash(text[start - 1 : start - 1 + width]),
                    text[start - 1],
                    text[start - 1 + width],
                    width,
                )
                assert rolled == window_hash(window), (width, text, start)


def test_the_roll_refuses_no_width() -> None:
    try:
        roll(1, "a", "b", 0)
    except HashError:
        return
    raise AssertionError("a widthless roll slipped through")


def test_the_windows_walk_the_text() -> None:
    assert windows("abra", 2) == ["ab", "br", "ra"]
    assert windows("ab", 5) == []
    try:
        windows("abra", 0)
    except HashError:
        return
    raise AssertionError("a widthless window list slipped through")
