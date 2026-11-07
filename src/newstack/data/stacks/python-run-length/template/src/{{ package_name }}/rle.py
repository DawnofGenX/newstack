"""Run-length encoding over lowercase letters: the counter itself.

encode(text) answers with the pair stream the stepper walks - one
(letter, count) per run, runs of one kept as honest pairs, stands
longer than MAX_RUN split into consecutive pairs of the same
letter so the sum stays the length. decode(pairs) replays every
pair letter by letter and answers the text. The rule every pair
keeps: a run is walked once and answered as a pair. The product
is the loop: decode(encode(text)) is the text, never an
approximation of it.
"""

from __future__ import annotations

from .pairs import (
    MAX_RUN,
    PairsError,
    normalise_pair,
    walk_runs,
)


class RunError(ValueError):
    """A pair stream broke on the way in or the way out."""

    __slots__ = ()


def encode(text: str) -> list:
    """The honest stream: the stepper's pairs, runs counted whole."""
    return list(walk_runs(text))


def decode(pairs: list) -> str:
    """Replay the stream: every pair writes its letter count times."""
    out: list[str] = []
    for pair in pairs:
        try:
            honest = normalise_pair(pair)
        except PairsError as failure:
            raise RunError(f"{failure}") from failure
        out.extend([honest.letter] * honest.count)
    return "".join(out)


def audit(pairs: list) -> list:
    """Walk the stream and name every pair the counter would refuse.

    Returns the named breaks and answers [] when the stream is
    honest: every letter a lowercase letter, every count a whole
    number between one and the ceiling, every row a pair.
    """
    breaks: list = []
    for index, pair in enumerate(pairs):
        try:
            honest = normalise_pair(pair)
        except PairsError as failure:
            breaks.append(f"pair {index}: {failure}")
            continue
        if honest.count > MAX_RUN:
            breaks.append(f"pair {index}: count {honest.count} past the ceiling")
    return breaks
