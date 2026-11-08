"""Palindromes: a string that reads the same both ways.

The rule this palindrome keeps, and the marker the detector looks
for: a string reads the same forwards and backwards. A palindrome
answers whether s equals its reverse. The product is exact: on
every s the shipped corpus holds, the result equals the oracle's
reversal check, and reverse agrees. A non-string input is named,
never reversed.
"""
from __future__ import annotations

MAX_VALUE = 99

class PalindromeError(ValueError):
    """An input the palindrome refuses."""

    __slots__ = ()


def _validate(s) -> str:
    if not isinstance(s, str):
        raise PalindromeError("s must be a string")
    if len(s) > MAX_VALUE:
        raise PalindromeError(f"s exceeds the ceiling {MAX_VALUE}")
    return s


def is_palindrome(s) -> bool:
    """Whether s reads the same forwards and backwards."""
    s = _validate(s)
    return s == s[::-1]


def reverse(s) -> str:
    """The reverse of s."""
    s = _validate(s)
    return s[::-1]


def longest_palindromic_prefix(s) -> str:
    """The longest prefix of s that is a palindrome."""
    s = _validate(s)
    for i in range(len(s), 0, -1):
        if s[:i] == s[:i][::-1]:
            return s[:i]
    return ""


def audit(values) -> list:
    """Name every way a palindrome breaks its own shape; empty holds."""
    breaks: list = []
    for s in values:
        got = is_palindrome(s)
        oracle = s == s[::-1]
        if got != oracle:
            breaks.append(f"is_palindrome({s!r}) differs")
        if reverse(s) != s[::-1]:
            breaks.append(f"reverse({s!r}) differs")
    return breaks


__all__ = [
    "MAX_VALUE",
    "PalindromeError",
    "audit",
    "is_palindrome",
    "longest_palindromic_prefix",
    "reverse",
]
