"""The stories this anagram tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, is_anagram, signature

    first = Story(
        "is_anagram('listen','silent')",
        f"is_anagram('listen','silent')={is_anagram('listen', 'silent')}",
        is_anagram("listen", "silent") is True,
    )
    second = Story(
        "is_anagram('abc','def')",
        f"is_anagram('abc','def')={is_anagram('abc', 'def')}",
        is_anagram("abc", "def") is False,
    )
    third = Story(
        "signature('abc')",
        f"signature('abc')={signature('abc')}",
        signature("abc") == ["a", "b", "c"],
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit([('listen', 'silent'), ('abc', 'def')])}",
        audit([("listen", "silent"), ("abc", "def")]) == [],
    )
    fifth = Story(
        "empty strings are anagrams",
        f"is_anagram('','')={is_anagram('', '')}",
        is_anagram("", "") is True,
    )
    sixth = Story(
        "a non-string is refused",
        "is_anagram refuses 5",
        _refuses_nonstr(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_nonstr() -> bool:
    from .solve import AnagramError, is_anagram

    try:
        is_anagram(5, "a")
    except AnagramError:
        return True
    return False
