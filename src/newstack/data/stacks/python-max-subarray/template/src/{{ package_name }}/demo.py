"""The stories this solver tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass

from .solve import audit, solve, witness


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    first = Story(
        "single",
        "solve([5]) == 5",
        solve([5]) == 5,
    )
    second = Story(
        "classic",
        "solve([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6",
        solve([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6,
    )
    third = Story(
        "all negative",
        "solve([-3, -2, -5]) == -2",
        solve([-3, -2, -5]) == -2,
    )
    fourth = Story(
        "witness sums",
        "sum(witness([-2, 1, -3, 4, -1, 2, 1, -5, 4])) == 6",
        sum(witness([-2, 1, -3, 4, -1, 2, 1, -5, 4])) == 6,
    )
    fifth = Story(
        "audit stays silent",
        "audit([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == []",
        audit([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == [],
    )
    sixth = Story(
        "two values",
        "solve([1, 2]) == 3",
        solve([1, 2]) == 3,
    )
    return [first, second, third, fourth, fifth, sixth]
