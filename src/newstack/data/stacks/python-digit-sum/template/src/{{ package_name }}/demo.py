"""The stories this digit sum tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, digit_count, digit_product, digit_sum

    first = Story(
        "digit_sum(1234)",
        f"digit_sum(1234)={digit_sum(1234)}",
        digit_sum(1234) == 10,
    )
    second = Story(
        "digit_product(1234)",
        f"digit_product(1234)={digit_product(1234)}",
        digit_product(1234) == 24,
    )
    third = Story(
        "digit_count(1234)",
        f"digit_count(1234)={digit_count(1234)}",
        digit_count(1234) == 4,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([1, 23, 456])}",
        audit([1, 23, 456]) == [],
    )
    fifth = Story(
        "digit_sum(0)",
        f"digit_sum(0)={digit_sum(0)}",
        digit_sum(0) == 0,
    )
    sixth = Story(
        "an oversized n is refused",
        "digit_sum refuses 10000",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import DigitSumError, digit_sum

    try:
        digit_sum(10000)
    except DigitSumError:
        return True
    return False
