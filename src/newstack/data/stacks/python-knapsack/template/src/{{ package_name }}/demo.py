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

    w = witness([2, 3, 4], [3, 4, 5], 5)
    fifth_held = sum([3, 4, 5][i] for i in w) == solve([2, 3, 4], [3, 4, 5], 5)

    first = Story("empty knapsack is zero", "solve([], [], 5) == 0", solve([], [], 5) == 0)
    second = Story("single item fits", "solve([2], [3], 5) == 3", solve([2], [3], 5) == 3)
    third = Story("single item too heavy", "solve([6], [3], 5) == 0", solve([6], [3], 5) == 0)
    fourth = Story(
        "classic instance",
        "solve([2, 3, 4], [3, 4, 5], 5) == 7",
        solve([2, 3, 4], [3, 4, 5], 5) == 7,
    )
    fifth = Story("witness matches optimum", "sum of witness values == solve", fifth_held)
    sixth = Story(
        "audit stays silent",
        "audit([2, 3, 4], [3, 4, 5], 5) == []",
        audit([2, 3, 4], [3, 4, 5], 5) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
