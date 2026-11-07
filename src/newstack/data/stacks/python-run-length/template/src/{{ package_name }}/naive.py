"""The literal-only oracle: one pair per letter, never more.

The oracle is deliberately slow and deliberately simple. It
collapses runs with a different path than the stepper - stdlib
grouping, not an index walk - and prices every text at one pair
per letter, the price a coder must never beat by being clever.
Where the stepper and the oracle disagree, the stepper is wrong.
"""

from __future__ import annotations

from itertools import groupby

from .rle import decode
from .text import ensure_text


def naive_encode(text: str) -> list:
    """The oracle stream: every letter its own honest pair of one."""
    source = ensure_text(text)
    return [(letter, 1) for letter in source]


def naive_decode(pairs: list) -> str:
    """The oracle read: replay one letter at a time, count by count."""
    out: list = []
    for row in pairs:
        letter, count = row[0], row[1]
        for _step in range(count):
            out.append(letter)
    return "".join(out)


def naive_price(text: str) -> int:
    """The ceiling a coder pays in pairs: one per letter, no more."""
    return len(ensure_text(text))


def naive_collapse(text: str) -> str:
    """The text with runs collapsed, walked by grouping not indices."""
    return "".join(letter for letter, _group in groupby(ensure_text(text)))


def naive_roundtrip(text: str) -> bool:
    """The oracle's own loop, and the coder's answer to the text."""
    source = ensure_text(text)
    return decode(naive_encode(source)) == source
