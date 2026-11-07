"""Six stories about the yard, the oracle, and what they owe each other.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calc import evaluate, value_of
from .oracle import descent
from .yard import postfix_text, to_postfix


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list:
    """The six claims the yard makes, each computed fresh."""
    expr = "3 + 4 * 2 / ( 1 - 5 ) ** 2"
    plain = "3 + 4 * 2 / ( 1 - 5 ) * 2"
    answer = value_of(plain)
    first = Story(
        "the yard and the oracle answer the same sum",
        f"{plain} = {answer} oracle={descent(plain)}",
        answer == descent(plain),
    )

    queue = postfix_text(to_postfix(plain))
    second = Story(
        "the queue the yard yields reckons to the value_of answer",
        f"postfix={queue!r} reckoned={evaluate(to_postfix(plain))}",
        evaluate(to_postfix(plain)) == answer,
    )

    tight = value_of("2 + 3 * 4")
    third = Story(
        "* parks tighter than +, the documented precedence",
        f"2 + 3 * 4 = {tight} oracle={descent('2 + 3 * 4')}",
        tight == 14 and tight == descent("2 + 3 * 4"),
    )

    floors = value_of("7 / 2")
    fourth = Story(
        "a division floors, 7 / 2 is three",
        f"7 / 2 = {floors} oracle={descent('7 / 2')}",
        floors == 3 == descent("7 / 2"),
    )

    left = value_of("100 - 20 - 5")
    fifth = Story(
        "every operator binds left, 100 - 20 - 5 is seventy-five",
        f"100 - 20 - 5 = {left} oracle={descent('100 - 20 - 5')}",
        left == 75 and left == descent("100 - 20 - 5"),
    )

    single = value_of("7")
    honest = all(
        value_of(one) == descent(one)
        for one in ("1 + 2", "( 1 + 2 ) * 3", "8 / 4 / 2", "2 * 3 + 4 * 5")
    )
    sixth = Story(
        "a lone number answers itself, the pairs stay equal",
        f"seven={single} expr={expr.count('(')} pairs_equal={honest}",
        single == 7 and honest,
    )
    return [first, second, third, fourth, fifth, sixth]
