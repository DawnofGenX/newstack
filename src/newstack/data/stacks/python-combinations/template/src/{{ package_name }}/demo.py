"""The stories this generator tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, combinations, count, unique

    sample = [1, 2, 3]
    grown = combinations(sample)
    first = Story(
        "every subset of three items is eight",
        f"count={len(grown)} power={count(3)} equal={len(grown) == count(3)}",
        len(grown) == count(3),
    )
    second = Story(
        "each entry is a true subset",
        f"subs={grown}",
        all(all(x in sample for x in s) for s in grown),
    )
    third = Story(
        "empty input yields one empty subset",
        f"subs={combinations([])}",
        combinations([]) == [()],
    )
    fourth = Story(
        "duplicates deduplicated by unique",
        f"unique(1,1,2)={unique([1,1,2])}",
        len(unique([1, 1, 2])) == len(set(combinations([1, 1, 2]))),
    )
    breaks = audit(sample)
    fifth = Story(
        "the audit stays silent",
        f"breaks={breaks}",
        breaks == [],
    )
    sixth = Story(
        "an oversized input is refused",
        "combinations refuses oversized",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import CombinationError, combinations

    try:
        combinations(list(range(9)))
    except CombinationError:
        return True
    return False
