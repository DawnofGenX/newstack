"""The stories this sieve tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, count_primes, is_prime, primes_up_to

    first = Story(
        "primes_up_to(10)",
        f"primes_up_to(10)={primes_up_to(10)}",
        primes_up_to(10) == [2, 3, 5, 7],
    )
    second = Story(
        "is_prime(7)",
        f"is_prime(7)={is_prime(7)}",
        is_prime(7) is True,
    )
    third = Story(
        "count_primes(10)",
        f"count_primes(10)={count_primes(10)}",
        count_primes(10) == 4,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([2, 5, 10, 30])}",
        audit([2, 5, 10, 30]) == [],
    )
    fifth = Story(
        "1 is not prime",
        "is_prime(1)=False",
        is_prime(1) is False,
    )
    sixth = Story(
        "a too-small n is refused",
        "primes_up_to refuses 1",
        _refuses_small(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_small() -> bool:
    from .solve import SieveError, primes_up_to

    try:
        primes_up_to(1)
    except SieveError:
        return True
    return False
