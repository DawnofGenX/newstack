"""The stories this word count tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, count_words, longest_word, word_frequencies

    first = Story(
        "count_words('a b c')",
        f"count_words('a b c')={count_words('a b c')}",
        count_words("a b c") == 3,
    )
    second = Story(
        "word_frequencies('a a b')",
        f"word_frequencies('a a b')={word_frequencies('a a b')}",
        word_frequencies("a a b") == {"a": 2, "b": 1},
    )
    third = Story(
        "longest_word('a bb ccc')",
        f"longest_word('a bb ccc')={longest_word('a bb ccc')}",
        longest_word("a bb ccc") == "ccc",
    )
    fourth = Story(
        "the audit stays silent",
        f"breaks={audit(['a b', 'x', ''])}",
        audit(["a b", "x", ""]) == [],
    )
    fifth = Story(
        "count_words('')",
        f"count_words('')={count_words('')}",
        count_words("") == 0,
    )
    sixth = Story(
        "an oversized s is refused",
        "count_words refuses a long string",
        _refuses_oversized(),
    )
    return [first, second, third, fourth, fifth, sixth]


def _refuses_oversized() -> bool:
    from .solve import WordCountError, count_words

    try:
        count_words("a" * 1001)
    except WordCountError:
        return True
    return False
