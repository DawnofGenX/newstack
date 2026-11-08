"""Bracket matching: a stack answers whether every bracket closes.

The rule this matcher keeps, and the marker the detector looks for:
every opening bracket must close in the right order, and a
mismatched or stray bracket is named. The stack is the honest
accountant of open brackets; pop the wrong one and the match fails.

Detect phrase: every opening bracket must close in the right order.
"""
from __future__ import annotations

MAX_LENGTH = 100

PAIRS = {"(": ")", "[": "]", "{": "}"}
OPENERS = set(PAIRS)
CLOSERS = set(PAIRS.values())


class BracketError(ValueError):
    """An input the matcher refuses."""

    __slots__ = ()


def _validate(text) -> str:
    if not isinstance(text, str):
        raise BracketError("text must be a string")
    if len(text) > MAX_LENGTH:
        raise BracketError(f"text exceeds the ceiling {MAX_LENGTH}")
    for ch in text:
        if ch not in OPENERS and ch not in CLOSERS:
            raise BracketError(f"unexpected character {ch!r}")
    return text


def is_valid(text) -> bool:
    text = _validate(text)
    stack = []
    for ch in text:
        if ch in OPENERS:
            stack.append(ch)
        else:
            if not stack or PAIRS[stack.pop()] != ch:
                return False
    return not stack


def matched_pairs(text) -> list:
    text = _validate(text)
    stack = []
    pairs = []
    for i, ch in enumerate(text):
        if ch in OPENERS:
            stack.append((ch, i))
        elif ch in CLOSERS:
            if stack and PAIRS[stack[-1][0]] == ch:
                _, j = stack.pop()
                pairs.append((j, i))
            else:
                return []
    if stack:
        return []
    return pairs


def count_unmatched(text) -> int:
    text = _validate(text)
    stack = 0
    unmatched = 0
    for ch in text:
        if ch in OPENERS:
            stack += 1
        else:
            if stack == 0:
                unmatched += 1
            else:
                stack -= 1
    return unmatched + stack


def audit(text) -> list:
    text = _validate(text)
    try:
        valid = is_valid(text)
    except BracketError:
        return ["invalid"]
    return [] if valid else ["mismatch"]


__all__ = [
    "MAX_LENGTH",
    "PAIRS",
    "BracketError",
    "audit",
    "count_unmatched",
    "is_valid",
    "matched_pairs",
]
