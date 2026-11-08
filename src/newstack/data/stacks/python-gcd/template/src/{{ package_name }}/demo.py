"""The stories this gcd tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, coprime, gcd, lcm

    first = Story(
        "gcd(12,8)=4",
        f"gcd(12,8)={gcd(12, 8)}",
        gcd(12, 8) == 4,
    )
    second = Story(
        "gcd(7,5)=1",
        f"gcd(7,5)={gcd(7, 5)}",
        gcd(7, 5) == 1,
    )
    third = Story(
        "lcm(4,6)=12",
        f"lcm(4,6)={lcm(4, 6)}",
        lcm(4, 6) == 12,
    )
    fourth = Story(
        "coprime(7,5)",
        f"coprime(7,5)={coprime(7, 5)}",
        coprime(7, 5) is True,
    )
    fifth = Story(
        "the audit stays silent",
        f"breaks={audit([(2, 4), (3, 5), (10, 15)])}",
        audit([(2, 4), (3, 5), (10, 15)]) == [],
    )
    sixth = Story(
        "a zero input is refused",
        "gcd refuses zero",
        _refuses_zero(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_zero() -> bool:
    from .solve import GcdError, gcd

    try:
        gcd(0, 5)
    except GcdError:
        return True
    return False
