"""Six stories about runs, pairs, and what a loop owes a text.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .naive import naive_collapse, naive_price
from .pairs import MAX_RUN, walk_runs
from .rle import audit, decode, encode


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list:
    """The six claims the counter makes, each computed fresh."""
    text = "abracadabrabananabracadabra"
    pairs = encode(text)
    first = Story(
        "the loop closes: decode hands back the letters encode was sent",
        f"letters={len(text)} pairs={len(pairs)} back={decode(pairs) == text}",
        decode(pairs) == text,
    )

    stepper = list(walk_runs(text))
    second = Story(
        "encode answers exactly what the stepper walks",
        f"encode={len(pairs)} stepper={len(stepper)} equal={pairs == stepper}",
        pairs == stepper,
    )

    run = "a" * 40
    paid = encode(run)
    third = Story(
        "a repeat pays in pairs, never in letters",
        f"letters={len(run)} pairs={len(paid)} cheaper={len(paid) < len(run)}",
        len(paid) < len(run) and decode(paid) == run,
    )

    capped = "b" * (MAX_RUN + 40)
    ceiling = encode(capped)
    fourth = Story(
        "a stand past the ceiling splits, the sum stays the length",
        f"letters={len(capped)} pairs={len(ceiling)} "
        f"sum={sum(pair.count for pair in ceiling)}",
        sum(pair.count for pair in ceiling) == len(capped)
        and all(pair.count <= MAX_RUN for pair in ceiling)
        and decode(ceiling) == capped,
    )

    collapsed = naive_collapse(text)
    walked = "".join(pair.letter for pair in walk_runs(text))
    fifth = Story(
        "the collapsed view is the stepper, letter for letter",
        f"collapsed={len(collapsed)} walked={len(walked)} equal={collapsed == walked}",
        collapsed == walked,
    )

    empty = encode("")
    honest = all(audit(encode(one)) == [] for one in (text, run, capped))
    sixth = Story(
        "the empty text is the empty stream, streams audit silent",
        f"empty_pairs={len(empty)} audits={honest} ceiling={MAX_RUN} "
        f"price={naive_price(text)}",
        empty == [] and decode([]) == "" and honest,
    )
    return [first, second, third, fourth, fifth, sixth]
