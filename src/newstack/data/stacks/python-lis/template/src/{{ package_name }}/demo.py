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
        "single value",
        "solve([5]) == 1",
        solve([5]) == 1,
    )
    second = Story(
        "already increasing",
        "solve([1, 2, 3]) == 3",
        solve([1, 2, 3]) == 3,
    )
    third = Story(
        "decreasing",
        "solve([3, 2, 1]) == 1",
        solve([3, 2, 1]) == 1,
    )
    fourth = Story(
        "classic",
        "solve([10, 9, 2, 5, 3, 7, 101, 18]) == 4",
        solve([10, 9, 2, 5, 3, 7, 101, 18]) == 4,
    )
    w = witness([10, 9, 2, 5, 3, 7, 101, 18])
    fifth = Story(
        "witness increasing",
        "witness is strictly increasing",
        all(w[k] < w[k + 1] for k in range(len(w) - 1)),
    )
    sixth = Story(
        "audit stays silent",
        "audit([1, 2, 3]) == []",
        audit([1, 2, 3]) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
