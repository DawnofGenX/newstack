"""The stories this generator tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, count, permutations, unique

    sample = [1, 2, 3]
    grown = permutations(sample)
    first = Story(
        "every ordering of three items is six",
        f"count={len(grown)} factorial={count(3)} equal={len(grown) == count(3)}",
        len(grown) == count(3),
    )
    second = Story(
        "each entry is a true permutation",
        f"perms={grown}",
        all(sorted(p) == sorted(sample) for p in grown),
    )
    third = Story(
        "empty input yields one empty ordering",
        f"perms={permutations([])}",
        permutations([]) == [()],
    )
    fourth = Story(
        "duplicates are deduplicated by unique",
        f"unique(1,1,2)={unique([1,1,2])}",
        len(unique([1, 1, 2])) == 3,
    )
    breaks = audit(sample)
    fifth = Story(
        "the audit stays silent",
        f"breaks={breaks}",
        breaks == [],
    )
    sixth = Story(
        "an oversized input is refused",
        "perm refuses oversized",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import PermutationError, permutations

    try:
        permutations(list(range(9)))
    except PermutationError:
        return True
    return False
