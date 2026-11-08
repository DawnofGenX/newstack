"""The stories this cipher tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    from .solve import audit, brute_force, decode, encode

    first = Story(
        "encode then decode recovers",
        "decode(encode('abc', 3), 3) == 'abc'",
        decode(encode("abc", 3), 3) == "abc",
    )
    second = Story(
        "shift zero is identity",
        "encode('abc', 0) == 'abc'",
        encode("abc", 0) == "abc",
    )
    third = Story(
        "wrap around works",
        "encode('xyz', 3) == 'abc'",
        encode("xyz", 3) == "abc",
    )
    fourth = Story(
        "non-letters stay put",
        "encode('a b!', 3) == 'd e!'",
        encode("a b!", 3) == "d e!",
    )
    fifth = Story(
        "brute force has 26 keys",
        "len(brute_force('abc')) == 26",
        len(brute_force("abc")) == 26,
    )
    sixth = Story(
        "audit stays silent",
        "audit('abc', 3) == []",
        audit("abc", 3) == [],
    )
    return [first, second, third, fourth, fifth, sixth]
