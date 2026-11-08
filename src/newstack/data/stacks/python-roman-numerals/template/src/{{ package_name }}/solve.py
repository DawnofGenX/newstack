"""Roman numerals: integers and their letter forms, both ways.

int_to_roman turns a positive integer into Roman digits, roman_to_int
reads a Roman string back into an integer, and audit reports any pair
that does not round-trip. Out-of-range or malformed inputs are named,
never converted.

subtractive notation trades one letter for four
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_ROMAN = 3999

ROMAN_PAIRS = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


class RomanError(ValueError):
    """Raised when an input is out of range or malformed."""


@dataclass(frozen=True)
class Break:
    left: int
    right: str
    reason: str


def _validate_decimal(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RomanError(f"decimal must be an int, got {type(value).__name__}")
    if value < 1:
        raise RomanError(f"decimal out of range: {value}")
    if value > MAX_ROMAN:
        raise RomanError(f"decimal too large: {value}")
    return value


ROMAN_CHARS = "IVXLCDM"
ROMAN_VALUE = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def _validate_roman(text: str) -> str:
    if not isinstance(text, str):
        raise RomanError(f"roman must be a str, got {type(text).__name__}")
    if not text:
        raise RomanError("empty roman string")
    if any(ch not in ROMAN_CHARS for ch in text):
        raise RomanError(f"malformed roman: {text!r}")
    return text


def int_to_roman(value: int) -> str:
    value = _validate_decimal(value)
    out: list[str] = []
    n = value
    for amount, letters in ROMAN_PAIRS:
        while n >= amount:
            out.append(letters)
            n -= amount
    return "".join(out)


def roman_to_int(text: str) -> int:
    text = _validate_roman(text)
    total = 0
    i = 0
    n = len(text)
    while i < n:
        if i + 1 < n and ROMAN_VALUE[text[i]] < ROMAN_VALUE[text[i + 1]]:
            total += ROMAN_VALUE[text[i + 1]] - ROMAN_VALUE[text[i]]
            i += 2
        else:
            total += ROMAN_VALUE[text[i]]
            i += 1
    return total


def audit(pairs: list[tuple[int, str]]) -> list[Break]:
    breaks: list[Break] = []
    for left, right in pairs:
        try:
            got = int_to_roman(left)
        except RomanError as exc:
            breaks.append(Break(left, right, str(exc)))
            continue
        if got != right:
            breaks.append(Break(left, right, f"int_to_roman({left}) = {got!r}, not {right!r}"))
            continue
        try:
            back = roman_to_int(right)
        except RomanError as exc:
            breaks.append(Break(left, right, str(exc)))
            continue
        if back != left:
            breaks.append(Break(left, right, f"roman_to_int({right!r}) = {back}, not {left}"))
    return breaks


__all__ = [
    "MAX_ROMAN",
    "Break",
    "RomanError",
    "audit",
    "int_to_roman",
    "roman_to_int",
]
