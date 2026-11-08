"""The stories this conversion tells, computed live."""

from __future__ import annotations

from dataclasses import dataclass

from .solve import HammingError, audit, hamming, hamming_text


@dataclass(frozen=True)
class Story:
    title: str
    detail: str
    held: bool


def _refuses() -> bool:
    try:
        hamming(1024, 0)
    except HammingError:
        return True
    return False


def stories() -> list:
    first = Story("bits 7,11", "ok", hamming(7, 11) == 2)
    second = Story("bits 0,0", "ok", hamming(0, 0) == 0)
    third = Story("chars abc,axc", "ok", hamming_text("abc", "axc") == 1)
    fourth = Story("audit silent", "ok", audit([(7, 11, 2), (0, 0, 0)]) == [])
    fifth = Story("chars empty", "ok", hamming_text("", "") == 0)
    sixth = Story("refused", "ok", _refuses())
    return [first, second, third, fourth, fifth, sixth]
