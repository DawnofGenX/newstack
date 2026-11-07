"""Seeded streams over ``[0, 256)``: same seed, same answers.

The audit needs streams nobody can fudge after the fact, so every
key comes from ``random.Random(seed)`` and the shipped ones are
frozen in the fixture. A stream is a plan for adding, key by key;
the filter must answer *present* to every earlier key after every
later update, and the fixture pins the arithmetic so a replay on a
fresh checkout raises the same bits.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .universe import UNIVERSE, ensure_seed

LENGTH = 32
FIXTURE = "fixtures/streams.txt"


class StreamError(ValueError):
    """A stream, seed, or fixture line cannot be used as given."""


def stream(seed: int, length: int = LENGTH) -> tuple[int, ...]:
    """The seeded draw: distinct keys from the universe, in order."""
    seed = ensure_seed(seed)
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise StreamError(f"length {length!r} is not a positive count")
    if length > UNIVERSE:
        raise StreamError(f"length {length} leaves the universe of {UNIVERSE}")
    drawn = random.Random(seed).sample(range(UNIVERSE), length)
    return tuple(drawn)


@dataclass(frozen=True)
class Plan:
    """One frozen add-stream: its seed, its length, its keys."""

    seed: int
    keys: tuple[int, ...]

    @property
    def length(self) -> int:
        return len(self.keys)

    @classmethod
    def draw(cls, seed: int, length: int = LENGTH) -> Plan:
        return cls(seed=ensure_seed(seed), keys=stream(seed, length))


def load_fixture(path: str) -> tuple[Plan, ...]:
    """Read the frozen streams; a comment is noise, a broken line is fatal."""
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as missing:
        raise StreamError(f"no stream fixture at {path}: {missing}") from None
    plans: list[Plan] = []
    for number, line in enumerate(lines, start=1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        words = text.split()
        try:
            seed = int(words[0])
            length = int(words[1])
            keys = tuple(int(word) for word in words[2:])
        except (ValueError, IndexError) as broken:
            raise StreamError(
                f"line {number} is no stream: {line.strip()!r} ({broken})"
            ) from None
        if len(keys) != length:
            raise StreamError(f"line {number}: promised {length}, holds {len(keys)}")
        plans.append(Plan(seed=seed, keys=keys))
    if not plans:
        raise StreamError(f"{path} freezes no streams")
    return tuple(plans)


def write_fixture(path: str, plans: tuple[Plan, ...]) -> None:
    """Freeze streams to disk; the header keeps the file honest to humans."""
    header = "# seeded add-streams over [0, 256): seed count key key ...\n"
    body = "".join(
        f"{plan.seed} {plan.length} " + " ".join(str(key) for key in plan.keys) + "\n"
        for plan in plans
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(header + body)
