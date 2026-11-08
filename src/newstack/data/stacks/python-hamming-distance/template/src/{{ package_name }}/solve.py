"""Hamming distance: how many positions disagree.

hamming counts the differing bits between two nonnegative integers,
hamming_text counts the differing characters between two equal-length
strings, and the audit reports any triple whose expected distance does
not match the computed one. Out-of-range or malformed inputs are
named, never measured.

hamming counts the bits that disagree
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_VALUE = 1023


class HammingError(ValueError):
    """Raised when an input is out of range or malformed."""


@dataclass(frozen=True)
class Break:
    left: int
    right: str
    reason: str


def _validate_int(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HammingError(f"value must be an int, got {type(value).__name__}")
    if value < 0:
        raise HammingError(f"negative value: {value}")
    if value > MAX_VALUE:
        raise HammingError(f"value too large: {value}")
    return value


def hamming(a: int, b: int) -> int:
    a = _validate_int(a)
    b = _validate_int(b)
    x = a ^ b
    count = 0
    while x:
        count += x & 1
        x >>= 1
    return count


def hamming_text(a: str, b: str) -> int:
    if not isinstance(a, str) or not isinstance(b, str):
        raise HammingError("both inputs must be str")
    if len(a) != len(b):
        raise HammingError(f"length mismatch: {len(a)} vs {len(b)}")
    return sum(1 for x, y in zip(a, b, strict=True) if x != y)


def audit(pairs: list[tuple[int, int, int]]) -> list[Break]:
    breaks: list[Break] = []
    for a, b, expected in pairs:
        try:
            got = hamming(a, b)
        except HammingError as exc:
            breaks.append(Break(a, f"{b},{expected}", str(exc)))
            continue
        if got != expected:
            breaks.append(
                Break(a, f"{b},{expected}", f"hamming({a}, {b}) = {got}, not {expected}")
            )
    return breaks


__all__ = [
    "MAX_VALUE",
    "Break",
    "HammingError",
    "audit",
    "hamming",
    "hamming_text",
]
