"""The stories this searcher tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, contains, lower_bound, search

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
        "lower_bound answers first >=",
        f"lower_bound(6)={lower_bound(arr, 6)}",
        lower_bound(arr, 6) == 3,
    )
    fifth = Story(
        "the audit stays silent",
        f"breaks={audit(arr, (1, 5, 13, 8))}",
        audit(arr, (1, 5, 13, 8)) == [],
    )
    sixth = Story(
        "an unsorted array is refused",
        "search refuses unsorted",
        _refuses_unsorted(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_unsorted() -> bool:
    from .solve import SearchError, search

    try:
        search((3, 1, 2), 1)
    except SearchError:
        return True
    return False
