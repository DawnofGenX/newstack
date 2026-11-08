"""The stories this conversion tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass

from .solve import RomanError, audit, int_to_roman, roman_to_int


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def _refuses() -> bool:
    try:
        int_to_roman(0)
    except RomanError:
        return True
    return False


def stories() -> list:
    first = Story("encode 1994", "ok", int_to_roman(1994) == "MCMXCIV")
    second = Story("decode MCMXCIV", "ok", roman_to_int("MCMXCIV") == 1994)
    third = Story("round trip", "ok", roman_to_int(int_to_roman(42)) == 42)
    fourth = Story("audit silent", "ok", audit([(42, "XLII"), (10, "X")]) == [])
    fifth = Story("decode I", "ok", roman_to_int("I") == 1)
    sixth = Story("refused", "ok", _refuses())
    return [first, second, third, fourth, fifth, sixth]
