"""The stories this matcher tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, count_unmatched, is_valid, matched_pairs

    first = Story(
        "a valid string validates",
        "is_valid('([])') is True",
        is_valid("([])") is True,
    )
    second = Story(
        "a mismatched string fails",
        "is_valid('([)]') is False",
        is_valid("([)]") is False,
    )
    third = Story(
        "matched pairs are listed",
        f"matched_pairs('([])') = {matched_pairs('([])')}",
        matched_pairs("([])") == [(1, 2), (0, 3)],
    )
    fourth = Story(
        "unmatched are counted",
        "count_unmatched('(((') == 3",
        count_unmatched("(((") == 3,
    )
    fifth = Story(
        "empty validates",
        "is_valid('') is True",
        is_valid("") is True,
    )
    sixth = Story(
        "audit stays silent",
        "audit('([])') == []",
        audit("([])") == [],
    )
    return [first, second, third, fourth, fifth, sixth]
