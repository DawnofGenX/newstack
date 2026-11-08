"""The stories this factorial tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, binomial, factorial

    first = Story(
        "factorial(5)=120",
        f"factorial(5)={factorial(5)}",
        factorial(5) == 120,
    )
    second = Story(
        "factorial(0)=1",
        f"factorial(0)={factorial(0)}",
        factorial(0) == 1,
    )
    third = Story(
        "binomial(5,2)=10",
        f"binomial(5,2)={binomial(5, 2)}",
        binomial(5, 2) == 10,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([0, 1, 5, 10])}",
        audit([0, 1, 5, 10]) == [],
    )
    fifth = Story(
        "binomial(5,0)=1",
        f"binomial(5,0)={binomial(5, 0)}",
        binomial(5, 0) == 1,
    )
    sixth = Story(
        "a negative n is refused",
        "factorial refuses -1",
        _refuses_neg(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_neg() -> bool:
    from .solve import FactorialError, factorial

    try:
        factorial(-1)
    except FactorialError:
        return True
    return False
