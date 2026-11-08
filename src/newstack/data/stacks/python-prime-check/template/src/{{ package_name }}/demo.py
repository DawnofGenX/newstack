"""The stories this prime check tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, is_prime, next_prime, prime_factors

    first = Story(
        "is_prime(17)",
        f"is_prime(17)={is_prime(17)}",
        is_prime(17) is True,
    )
    second = Story(
        "is_prime(1)",
        f"is_prime(1)={is_prime(1)}",
        is_prime(1) is False,
    )
    third = Story(
        "next_prime(10)",
        f"next_prime(10)={next_prime(10)}",
        next_prime(10) == 11,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([2, 3, 4, 5, 10])}",
        audit([2, 3, 4, 5, 10]) == [],
    )
    fifth = Story(
        "prime_factors(12)",
        f"prime_factors(12)={prime_factors(12)}",
        prime_factors(12) == [2, 2, 3],
    )
    sixth = Story(
        "an oversized n is refused",
        "is_prime refuses 10000",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import PrimeCheckError, is_prime

    try:
        is_prime(10000)
    except PrimeCheckError:
        return True
    return False
