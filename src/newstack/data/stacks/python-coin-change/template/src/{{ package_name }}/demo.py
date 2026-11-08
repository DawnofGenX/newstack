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
        "zero amount needs no coins",
        "solve([1, 2, 5], 0) == 0",
        solve([1, 2, 5], 0) == 0,
    )
    second = Story(
        "exact coin",
        "solve([1, 2, 5], 5) == 1",
        solve([1, 2, 5], 5) == 1,
    )
    third = Story(
        "needs two coins",
        "solve([1, 2, 5], 6) == 2",
        solve([1, 2, 5], 6) == 2,
    )
    fourth = Story(
        "impossible amount",
        "solve([2, 4], 3) == -1",
        solve([2, 4], 3) == -1,
    )
    w = witness([1, 2, 5], 6)
    fifth = Story(
        "witness sums to amount",
        "sum(witness) == amount",
        sum(w) == 6,
    )
    sixth = Story(
        "audit stays silent",
        "audit([1, 2, 5], 6) == []",
        audit([1, 2, 5], 6) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
