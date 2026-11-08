"""The stories this lcs tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, lcs, lcs_length

    first = Story("lcs abcde ace", "lcs", lcs("abcde", "ace") == "ace")
    second = Story("length agrees", "len", lcs_length("abcde", "ace") == 3)
    third = Story("empty input", f"lcs('','abc')={lcs('','abc')!r}", lcs("", "abc") == "")
    fourth = Story("audit silent", "breaks", audit([("abcde", "ace"), ("abc", "abc")]) == [])
    fifth = Story("identical strings", "lcs('abc','abc')", lcs("abc", "abc") == "abc")
    sixth = Story("an oversized n is refused", "lcs refuses 65 chars", _refuses())
    return [first, second, third, fourth, fifth, sixth]


def _refuses() -> bool:
    from .solve import LcsError, lcs

    try:
        lcs("a" * 65, "b")
    except LcsError:
        return True
    return False
