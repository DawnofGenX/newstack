from __future__ import annotations

from {{ package_name }}.values import (
    ValueRejection,
    describe,
    ensure_value,
    step_size,
)


def test_the_value_comes_back_itself() -> None:
    assert ensure_value(7) == 7
    assert ensure_value(-40) == -40
    assert ensure_value(0) == 0


def test_a_value_renders_as_itself() -> None:
    assert describe(42) == "42"
    assert describe(-7) == "-7"


def test_the_step_is_a_lowest_bit() -> None:
    assert step_size(6) == 2
    assert step_size(12) == 4
    assert step_size(9) == 1


def test_a_non_number_is_refused() -> None:
    for stranger in ([1], "seven", 1.0, True, None):
        try:
            ensure_value(stranger)
        except ValueRejection:
            continue
        raise AssertionError(f"{stranger!r} should not stand in a cell")


def test_a_stranger_takes_no_step() -> None:
    for stranger in ("six", 0, -3, None):
        try:
            step_size(stranger)  # type: ignore[arg-type]
        except ValueRejection:
            continue
        raise AssertionError(f"{stranger!r} should have no step")
