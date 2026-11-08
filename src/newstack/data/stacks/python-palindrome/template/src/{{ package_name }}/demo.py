"""The stories this palindrome tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, is_palindrome, reverse

    first = Story(
        "is_palindrome('aba')",
        f"is_palindrome('aba')={is_palindrome('aba')}",
        is_palindrome("aba") is True,
    )
    second = Story(
        "is_palindrome('ab')",
        f"is_palindrome('ab')={is_palindrome('ab')}",
        is_palindrome("ab") is False,
    )
    third = Story(
        "reverse('ab')",
        f"reverse('ab')={reverse('ab')}",
        reverse("ab") == "ba",
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit(['aba', 'ab', 'a', ''])}",
        audit(["aba", "ab", "a", ""]) == [],
    )
    fifth = Story(
        "empty is a palindrome",
        f"is_palindrome('')={is_palindrome('')}",
        is_palindrome("") is True,
    )
    sixth = Story(
        "a non-string is refused",
        "is_palindrome refuses 5",
        _refuses_nonstr(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_nonstr() -> bool:
    from .solve import PalindromeError, is_palindrome

    try:
        is_palindrome(5)
    except PalindromeError:
        return True
    return False
