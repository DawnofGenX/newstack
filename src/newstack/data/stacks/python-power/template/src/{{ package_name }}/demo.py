"""The stories this power tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, fast_pow, pow_mod

    first = Story("fast_pow(2, 10)", f"fast_pow={fast_pow(2, 10)}", fast_pow(2, 10) == 1024)
    second = Story("fast_pow(3, 0)", f"fast_pow={fast_pow(3, 0)}", fast_pow(3, 0) == 1)
    third = Story("pow_mod", "pow_mod", pow_mod(2, 10, 1000) == 24)
    fourth = Story("audit silent", "breaks", audit([(2, 10), (3, 5), (5, 0)]) == [])
    fifth = Story("fast_pow(0, 5)", f"fast_pow={fast_pow(0, 5)}", fast_pow(0, 5) == 0)
    sixth = Story("an oversized exponent is refused", "power refuses 1001", _refuses())
    return [first, second, third, fourth, fifth, sixth]


def _refuses() -> bool:
    from .solve import PowerError, fast_pow

    try:
        fast_pow(2, 1001)
    except PowerError:
        return True
    return False
