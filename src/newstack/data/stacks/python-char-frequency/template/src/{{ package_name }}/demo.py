"""The stories this character frequency tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, char_frequencies, count_chars, most_common

    first = Story(
        "count_chars('a b')",
        f"count_chars('a b')={count_chars('a b')}",
        count_chars("a b") == 3,
    )
    second = Story(
        "char_frequencies('aab')",
        f"char_frequencies('aab')={char_frequencies('aab')}",
        char_frequencies("aab") == {"a": 2, "b": 1},
    )
    third = Story(
        "most_common('aab')",
        f"most_common('aab')={most_common('aab')}",
        most_common("aab") == "a",
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit(['a b', 'x', ''])}",
        audit(["a b", "x", ""]) == [],
    )
    fifth = Story(
        "count_chars('')",
        f"count_chars('')={count_chars('')}",
        count_chars("") == 0,
    )
    sixth = Story(
        "an oversized s is refused",
        "count_chars refuses a long string",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import CharFrequencyError, count_chars

    try:
        count_chars("a" * 1001)
    except CharFrequencyError:
        return True
    return False
