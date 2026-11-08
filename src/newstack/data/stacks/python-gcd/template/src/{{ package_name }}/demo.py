"""The stories this gcd tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, extended_gcd, gcd, mod_inverse

    first = Story(
        "gcd(4, 6)",
        f"gcd(4, 6)={gcd(4, 6)}",
        gcd(4, 6) == 2,
    )
    second = Story(
        "extended_gcd(4, 6)",
        f"extended_gcd(4, 6)={extended_gcd(4, 6)}",
        extended_gcd(4, 6)[0] == 2,
    )
    third = Story(
        "mod_inverse(3, 7)",
        f"mod_inverse(3, 7)={mod_inverse(3, 7)}",
        mod_inverse(3, 7) == 5,
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([(4, 6), (3, 5), (7, 7)])}",
        audit([(4, 6), (3, 5), (7, 7)]) == [],
    )
    fifth = Story(
        "gcd(0, 5)",
        f"gcd(0, 5)={gcd(0, 5)}",
        gcd(0, 5) == 5,
    )
    sixth = Story(
        "an oversized n is refused",
        "gcd refuses 10000",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import GcdError, gcd

    try:
        gcd(10000, 2)
    except GcdError:
        return True
    return False
