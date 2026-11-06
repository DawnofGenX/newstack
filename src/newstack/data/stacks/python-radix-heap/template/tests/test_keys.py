from __future__ import annotations

from {{ package_name }}.keys import (
    KeyValueError,
    describe,
    ensure_key,
    seat_of,
)


def test_the_key_comes_back_itself() -> None:
    assert ensure_key(7) == 7
    assert ensure_key(0) == 0


def test_a_key_renders_as_itself() -> None:
    assert describe(42) == "42"
    assert describe(0) == "0"


def test_a_seat_is_a_bit_length() -> None:
    assert seat_of(0, 0) == 0
    assert seat_of(8, 0) == 4
    assert seat_of(63, 64) == 7


def test_a_non_number_is_refused() -> None:
    for stranger in ([1], "seven", 1.0, True, None):
        try:
            ensure_key(stranger)
        except KeyValueError:
            continue
        raise AssertionError(f"{stranger!r} should not take a seat")


def test_a_non_number_takes_no_seat() -> None:
    try:
        seat_of("seven", 0)  # type: ignore[arg-type]
    except KeyValueError:
        return
    raise AssertionError("a string should not take a seat")
