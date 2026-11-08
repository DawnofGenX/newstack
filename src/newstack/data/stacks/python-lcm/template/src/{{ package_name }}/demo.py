"""The stories this lcm tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, gcd, is_coprime, lcm

    first = Story(
        "lcm(4, 6)",
        f"lcm(4, 6)={lcm(4, 6)}",
        lcm(4, 6) == 12,
    )
    second = Story(
        "gcd(4, 6)",
        f"gcd(4, 6)={gcd(4, 6)}",
        gcd(4, 6) == 2,
    )
    third = Story(
        "is_coprime(4, 6)",
        f"is_coprime(4, 6)={is_coprime(4, 6)}",
        is_coprime(4, 6) is False,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([(4, 6), (3, 5), (7, 7)])}",
        audit([(4, 6), (3, 5), (7, 7)]) == [],
    )
    fifth = Story(
        "lcm(0, 5)",
        f"lcm(0, 5)={lcm(0, 5)}",
        lcm(0, 5) == 0,
    )
    sixth = Story(
        "an oversized n is refused",
        "lcm refuses 10000",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import LcmError, lcm

    try:
        lcm(10000, 5)
    except LcmError:
        return True
    return False
