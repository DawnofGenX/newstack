"""Fast exponentiation over small integers.

The rule this power keeps, and the marker the detector looks for:
squaring halves the work, multiplying keeps the base. A fast pow
answers base**exponent by repeated squaring.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_EXPONENT = 1000
MAX_BASE = 1000


class PowerError(ValueError):
    """Raised when a request cannot be honoured."""


@dataclass(frozen=True)
class Break:
    base: int
    exponent: int
    reason: str


def _validate_int(value, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PowerError(f"{name} must be an int, got {type(value).__name__}")
    return value


def _check_range(base: int, exponent: int) -> None:
    if base < 0 or base > MAX_BASE:
        raise PowerError(f"base out of range: {base}")
    if exponent < 0 or exponent > MAX_EXPONENT:
        raise PowerError(f"exponent out of range: {exponent}")


def fast_pow(base: int, exponent: int) -> int:
    base = _validate_int(base, "base")
    exponent = _validate_int(exponent, "exponent")
    _check_range(base, exponent)
    result = 1
    cur = base
    e = exponent
    while e > 0:
        if e & 1:
            result *= cur
        cur *= cur
        e >>= 1
    return result


def pow_mod(base: int, exponent: int, modulus: int) -> int:
    base = _validate_int(base, "base")
    exponent = _validate_int(exponent, "exponent")
    modulus = _validate_int(modulus, "modulus")
    if modulus <= 0:
        raise PowerError(f"modulus must be positive, got {modulus}")
    _check_range(base, exponent)
    result = 1 % modulus
    cur = base % modulus
    e = exponent
    while e > 0:
        if e & 1:
            result = (result * cur) % modulus
        cur = (cur * cur) % modulus
        e >>= 1
    return result


def audit(pairs: list[tuple[int, int]]) -> list[Break]:
    breaks: list[Break] = []
    for base, exponent in pairs:
        try:
            got = fast_pow(base, exponent)
        except PowerError as exc:
            breaks.append(Break(base, exponent, str(exc)))
            continue
        want = 1
        for _ in range(exponent):
            want *= base
        if got != want:
            breaks.append(Break(base, exponent, "mismatch"))
    return breaks


__all__ = ["MAX_BASE", "MAX_EXPONENT", "Break", "PowerError", "audit", "fast_pow", "pow_mod"]
