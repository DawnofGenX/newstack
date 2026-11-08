"""The stories this armstrong check tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import armstrong_sum, audit, is_armstrong

    first = Story(
        "is_armstrong(153)",
        f"is_armstrong(153)={is_armstrong(153)}",
        is_armstrong(153) is True,
    )
    second = Story(
        "is_armstrong(10)",
        f"is_armstrong(10)={is_armstrong(10)}",
        is_armstrong(10) is False,
    )
    third = Story(
        "armstrong_sum(153)",
        f"armstrong_sum(153)={armstrong_sum(153)}",
        armstrong_sum(153) == 153,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([153, 370, 371])}",
        audit([153, 370, 371]) == [],
    )
    fifth = Story(
        "is_armstrong(0)",
        f"is_armstrong(0)={is_armstrong(0)}",
        is_armstrong(0) is True,
    )
    sixth = Story(
        "an oversized n is refused",
        "is_armstrong refuses 10000",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import ArmstrongError, is_armstrong

    try:
        is_armstrong(10000)
    except ArmstrongError:
        return True
    return False
