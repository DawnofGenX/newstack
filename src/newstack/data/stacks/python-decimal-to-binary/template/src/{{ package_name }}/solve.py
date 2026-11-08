"""Decimal to binary conversion: two bases, one round trip.

dec_to_binary turns a nonnegative integer into its base-two digits,
binary_to_decimal reads a binary string back into an integer, and the
audit reports any pair that does not round-trip. Oversized or malformed
inputs are named, never converted.

decimal to binary is division by two, binary to decimal is powers of two
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_DECIMAL = 1023


class ConversionError(ValueError):
    """Raised when an input is out of range or malformed."""


@dataclass(frozen=True)
class Break:
    left: int
    right: str
    reason: str


def _validate_decimal(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConversionError(f"decimal must be an int, got {type(value).__name__}")
    if value < 0:
        raise ConversionError(f"negative decimal: {value}")
    if value > MAX_DECIMAL:
        raise ConversionError(f"decimal too large: {value}")
    return value


def _validate_binary(text: str) -> str:
    if not isinstance(text, str):
        raise ConversionError(f"binary must be a str, got {type(text).__name__}")
    if not text:
        raise ConversionError("empty binary string")
    if any(ch not in "01" for ch in text):
        raise ConversionError(f"malformed binary: {text!r}")
    return text


def dec_to_binary(value: int) -> str:
    value = _validate_decimal(value)
    if value == 0:
        return "0"
    digits: list[str] = []
    n = value
    while n > 0:
        digits.append(str(n % 2))
        n //= 2
    digits.reverse()
    return "".join(digits)


def binary_to_decimal(text: str) -> int:
    text = _validate_binary(text)
    total = 0
    for ch in text:
        total = total * 2 + (1 if ch == "1" else 0)
    return total


def audit(pairs: list[tuple[int, str]]) -> list[Break]:
    breaks: list[Break] = []
    for left, right in pairs:
        try:
            got = dec_to_binary(left)
        except ConversionError as exc:
            breaks.append(Break(left, right, str(exc)))
            continue
        if got != right:
            breaks.append(Break(left, right, f"dec_to_binary({left}) = {got!r}, not {right!r}"))
            continue
        try:
            back = binary_to_decimal(right)
        except ConversionError as exc:
            breaks.append(Break(left, right, str(exc)))
            continue
        if back != left:
            breaks.append(Break(left, right, f"binary_to_decimal({right!r}) = {back}, not {left}"))
    return breaks


__all__ = [
    "MAX_DECIMAL",
    "Break",
    "ConversionError",
    "audit",
    "binary_to_decimal",
    "dec_to_binary",
]