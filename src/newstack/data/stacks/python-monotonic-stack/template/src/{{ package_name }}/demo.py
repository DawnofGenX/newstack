"""The stories this monotonic stack tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass

from .solve import next_greater, next_smaller, previous_greater


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    sample = [2, 1, 3]
    greater = next_greater(sample)
    smaller = next_smaller(sample)
    previous = previous_greater(sample)
    first = Story(
        "next greater finds the first larger value to the right",
        f"sample={sample} greater={greater}",
        greater == [3, 3, None],
    )
    second = Story(
        "next smaller finds the first smaller value to the right",
        f"sample={sample} smaller={smaller}",
        smaller == [1, None, None],
    )
    third = Story(
        "previous greater finds the nearest larger value to the left",
        f"sample={sample} previous={previous}",
        previous == [None, 2, None],
    )
    fourth = Story(
        "an increasing list points each value to the next",
        "input=[1,2,3,4,5] greater=[2,3,4,5,None]",
        next_greater([1, 2, 3, 4, 5]) == [2, 3, 4, 5, None],
    )
    fifth = Story(
        "a decreasing list has no greater neighbour",
        "input=[5,4,3,2,1] greater all None",
        all(x is None for x in next_greater([5, 4, 3, 2, 1])),
    )
    sixth = Story(
        "an empty list stays empty",
        "input=[] greater=[]",
        next_greater([]) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
