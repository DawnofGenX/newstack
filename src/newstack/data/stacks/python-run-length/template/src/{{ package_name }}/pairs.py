"""A pair is one letter and the honest length of its run.

A run is walked once and answered as a pair: the letter and how
many times it stood together. walk_runs is the stepper - it walks
the text once, pausing at each run, and answers Pair(letter, count)
for every stand. A count starts at one - a run of one is an honest
pair, never a bare letter - and stops at MAX_RUN, the documented
ceiling, so a longer stand splits into consecutive pairs of the
same letter and the sum stays the truth.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from .text import ensure_text

MAX_RUN = 255


class PairsError(ValueError):
    """A pair or a pair stream is not what the counter ships."""

    __slots__ = ()


@dataclass(frozen=True)
class Pair:
    """One letter and how many times it stood together."""

    letter: str
    count: int

    def __post_init__(self) -> None:
        if self.letter not in "abcdefghijklmnopqrstuvwxyz":
            raise PairsError(f"{self.letter!r} is no lowercase letter")
        if not isinstance(self.count, int) or isinstance(self.count, bool):
            raise PairsError(f"{self.count!r} is no count")
        if self.count < 1:
            raise PairsError(f"{self.count} is no count, runs start at one")
        if self.count > MAX_RUN:
            raise PairsError(f"{self.count} is past the {MAX_RUN} ceiling")


def normalise_pair(pair: object) -> Pair:
    """Accept a Pair or a (letter, count) tuple, answer a Pair."""
    if isinstance(pair, Pair):
        return pair
    if isinstance(pair, tuple) and len(pair) == 2:
        return Pair(pair[0], pair[1])
    raise PairsError(f"{pair!r} is no pair")


def walk_runs(text: str) -> Iterator[Pair]:
    """The stepper: walk the text once, answer each run in order."""
    source = ensure_text(text)
    index = 0
    while index < len(source):
        letter = source[index]
        count = 1
        while index + count < len(source) and source[index + count] == letter:
            count += 1
        total = count
        while count > MAX_RUN:
            yield Pair(letter, MAX_RUN)
            count -= MAX_RUN
        yield Pair(letter, count)
        index += total


def pairs_to_json(pairs: list) -> str:
    """The pair stream's JSON face: [["a", 3], ["b", 1]]."""
    rows = [[pair.letter, pair.count] for pair in (normalise_pair(p) for p in pairs)]
    return json.dumps(rows)


def pairs_from_json(payload: str) -> list:
    """The JSON face in, the pair stream out, noise refused."""
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError as failure:
        raise PairsError(f"not JSON: {failure}") from failure
    if not isinstance(rows, list):
        raise PairsError(f"{payload[:40]!r} holds no pair stream")
    pairs: list = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 2:
            raise PairsError(f"{row!r} is no pair row")
        pairs.append(Pair(row[0], row[1]))
    return pairs
