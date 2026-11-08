"""The stories this vowel count tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, count_vowels, is_vowel, vowel_positions

    first = Story(
        "count_vowels('hello')",
        f"count_vowels('hello')={count_vowels('hello')}",
        count_vowels("hello") == 2,
    )
    second = Story(
        "is_vowel('a')",
        f"is_vowel('a')={is_vowel('a')}",
        is_vowel("a") is True,
    )
    third = Story(
        "vowel_positions('hello')",
        f"vowel_positions('hello')={vowel_positions('hello')}",
        vowel_positions("hello") == [1, 4],
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit(['hello', 'xyz', 'AEIOU'])}",
        audit(["hello", "xyz", "AEIOU"]) == [],
    )
    fifth = Story(
        "AEIOU all vowels",
        f"count_vowels('AEIOU')={count_vowels('AEIOU')}",
        count_vowels("AEIOU") == 5,
    )
    sixth = Story(
        "a non-string is refused",
        "count_vowels refuses 5",
        _refuses_nonstr(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_nonstr() -> bool:
    from .solve import VowelCountError, count_vowels

    try:
        count_vowels(5)
    except VowelCountError:
        return True
    return False
