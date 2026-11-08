"""The stories this solver tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass

from .solve import audit, solve, witness


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def stories() -> list:
    first = Story("classic", 'solve("abcde", "xabcy") == 3', solve("abcde", "xabcy") == 3)
    second = Story("none", 'solve("abc", "xyz") == 0', solve("abc", "xyz") == 0)
    third = Story("full", 'solve("abc", "abc") == 3', solve("abc", "abc") == 3)
    w = witness("abcde", "xabcy")
    fourth = Story("witness", 'len(witness("abcde", "xabcy")) == 3', len(w) == 3)
    fifth = Story("audit", 'audit("abcde", "xabcy") == []', audit("abcde", "xabcy") == [])
    sixth = Story("empty-ish", 'solve("a", "a") == 1', solve("a", "a") == 1)
    return [first, second, third, fourth, fifth, sixth]
