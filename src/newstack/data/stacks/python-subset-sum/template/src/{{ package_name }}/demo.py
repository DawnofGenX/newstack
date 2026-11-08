"""The stories this solver tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, solve, witness

    first = Story(
        "empty subset",
        "solve([], 0) is True",
        solve([], 0) is True,
    )
    second = Story(
        "single match",
        "solve([5], 5) is True",
        solve([5], 5) is True,
    )
    third = Story(
        "no match",
        "solve([1, 2], 4) is False",
        solve([1, 2], 4) is False,
    )
    fourth = Story(
        "classic",
        "solve([3, 34, 4, 12, 5, 2], 9) is True",
        solve([3, 34, 4, 12, 5, 2], 9) is True,
    )
    w = witness([3, 34, 4, 12, 5, 2], 9)
    fifth = Story(
        "witness sums",
        "sum(witness) == 9",
        sum(w) == 9,
    )
    sixth = Story(
        "audit stays silent",
        "audit([3, 34, 4, 12, 5, 2], 9) == []",
        audit([3, 34, 4, 12, 5, 2], 9) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
