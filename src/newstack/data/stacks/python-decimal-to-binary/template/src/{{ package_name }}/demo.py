"""The stories this conversion tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, binary_to_decimal, dec_to_binary

    first = Story("dec_to_binary(10)", "ok", dec_to_binary(10) == "1010")
    second = Story("dec_to_binary(0)", "ok", dec_to_binary(0) == "0")
    third = Story("binary_to_decimal", "ok", binary_to_decimal("1010") == 10)
    fourth = Story("audit silent", "ok", audit([(10, "1010"), (7, "111")]) == [])
    fifth = Story("binary_to_decimal(0)", "ok", binary_to_decimal("0") == 0)
    sixth = Story("refused", "ok", _refuses())
    return [first, second, third, fourth, fifth, sixth]


def _refuses() -> bool:
    from .solve import ConversionError, dec_to_binary

    try:
        dec_to_binary(1024)
    except ConversionError:
        return True
    return False