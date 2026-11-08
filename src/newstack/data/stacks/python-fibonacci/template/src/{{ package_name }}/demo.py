"""The stories this fibonacci tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, fibonacci, fibonacci_list

    first = Story(
        "fibonacci(10)=55",
        f"fibonacci(10)={fibonacci(10)}",
        fibonacci(10) == 55,
    )
    second = Story(
        "fibonacci(0)=0",
        f"fibonacci(0)={fibonacci(0)}",
        fibonacci(0) == 0,
    )
    third = Story(
        "fibonacci_list(5)",
        f"fibonacci_list(5)={fibonacci_list(5)}",
        fibonacci_list(5) == [0, 1, 1, 2, 3],
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([0, 1, 5, 10])}",
        audit([0, 1, 5, 10]) == [],
    )
    fifth = Story(
        "fibonacci(1)=1",
        f"fibonacci(1)={fibonacci(1)}",
        fibonacci(1) == 1,
    )
    sixth = Story(
        "a negative n is refused",
        "fibonacci refuses -1",
        _refuses_neg(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_neg() -> bool:
    from .solve import FibonacciError, fibonacci

    try:
        fibonacci(-1)
    except FibonacciError:
        return True
    return False
