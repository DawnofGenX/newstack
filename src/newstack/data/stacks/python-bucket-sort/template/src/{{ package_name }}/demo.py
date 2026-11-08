"""The stories this sorter tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, counts, rank, sort

    sample = (3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5)
    grown = sort(sample)
    least = sorted(sample)
    first = Story(
        "the sort answers the oracle's list, entry for entry",
        f"sorted={grown} oracle={least} equal={grown == least}",
        grown == least,
    )
    second = Story(
        "the sort is stable: equal keys keep input order",
        f"input={sample} sorted={grown}",
        grown == sorted(sample),
    )
    tally = counts(sample)
    third = Story(
        "the tally is the histogram",
        f"tally={tally}",
        all(tally[v] == sample.count(v) for v in set(sample)),
    )
    fourth = Story(
        "the rank is the prefix count",
        f"rank(5)={rank(sample, 5)}",
        rank(sample, 5) == sum(1 for v in sample if v <= 5),
    )
    breaks = audit(sample)
    fifth = Story(
        "the audit stays silent",
        f"breaks={breaks}",
        breaks == [],
    )
    sixth = Story(
        "a negative value is refused",
        "sort refuses negatives",
        _refuses_negative(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_negative() -> bool:
    from .solve import SortError, sort

    try:
        sort((1, -1, 2))
    except SortError:
        return True
    return False
