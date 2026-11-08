"""The stories this searcher tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, contains, count, search

    arr = (1, 3, 5, 7, 9, 11, 13)
    first = Story(
        "a hit answers its index",
        f"search(7)={search(arr, 7)}",
        search(arr, 7) == 3,
    )
    second = Story(
        "a miss answers -1",
        f"search(8)={search(arr, 8)}",
        search(arr, 8) == -1,
    )
    third = Story(
        "contains reports presence",
        f"contains(5)={contains(arr, 5)}",
        contains(arr, 5) is True,
    )
    fourth = Story(
        "count answers the tally",
        f"count(5)={count(arr, 5)}",
        count(arr, 5) == 1,
    )
    fifth = Story(
        "the audit stays silent",
        f"breaks={audit(arr, (1, 5, 13, 8))}",
        audit(arr, (1, 5, 13, 8)) == [],
    )
    sixth = Story(
        "an out-of-range target is refused",
        "search refuses out-of-range",
        _refuses_oor(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oor() -> bool:
    from .solve import SearchError, search

    try:
        search((1, 2, 3), 999)
    except SearchError:
        return True
    return False
