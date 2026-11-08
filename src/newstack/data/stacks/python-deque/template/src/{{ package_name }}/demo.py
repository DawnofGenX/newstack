"""The stories this deque tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import append_left, make_deque, pop, pop_left, rotate, to_list

    first = Story(
        "both ends are first-class",
        f"appendleft 0 -> {to_list(append_left(make_deque([1, 2, 3]), 0))}",
        to_list(append_left(make_deque([1, 2, 3]), 0)) == [0, 1, 2, 3],
    )
    second = Story(
        "pop mirrors push",
        "pop returns the last appended",
        pop(make_deque([1, 2, 3])) == 3 and to_list(make_deque([1, 2])) == [1, 2],
    )
    third = Story(
        "rotation keeps every item",
        f"rotate(1) of [1,2,3] = {to_list(rotate(make_deque([1, 2, 3]), 1))}",
        sorted(to_list(rotate(make_deque([1, 2, 3]), 1))) == [1, 2, 3],
    )
    fourth = Story(
        "popleft removes the leftmost",
        "popleft returns 1",
        pop_left(make_deque([1, 2, 3])) == 1,
    )
    fifth = Story(
        "peek does not remove",
        "peek returns last, size unchanged",
        peek_right_ok(),
    )
    sixth = Story(
        "empty is refused",
        "pop on empty raises",
        refuses_empty(),
    )
    return [first, second, third, fourth, fifth, sixth]


def peek_right_ok() -> bool:
    from .solve import make_deque, peek, to_list

    d = make_deque([1, 2, 3])
    before = to_list(d)
    got = peek(d)
    return got == 3 and to_list(d) == before


def refuses_empty() -> bool:
    from .solve import DequeError, make_deque, pop

    try:
        pop(make_deque([]))
    except DequeError:
        return True
    return False
