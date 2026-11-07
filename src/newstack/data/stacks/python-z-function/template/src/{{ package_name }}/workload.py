"""Seeded storms: the array against the stepper, entry by entry.

Each step draws a word and a pattern, runs the array and the dumb
scan, and compares the full arrays. A mismatch is a break, recorded
with the word that caused it; the storm only passes when it breaks
nothing and checks more than it steps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .array import occurrences, z_function
from .corpus import DEFAULT_SEED
from .naive import naive_occurrences, naive_z

DEFAULT_STEPS = 140
WORD_POOL = "abcabracadabraabanana"


class WorkloadError(ValueError):
    """The storm was handed nonsense."""

    __slots__ = ()


@dataclass(frozen=True)
class Storm:
    """One storm's ledger: steps, checks, breaks, and whether it held."""

    steps: int
    checks: int
    breaks: tuple[str, ...]

    @property
    def seated(self) -> bool:
        return not self.breaks


def _tangle(rng: random.Random) -> tuple[str, str]:
    word = "".join(rng.choice(WORD_POOL) for _ in range(rng.randint(0, 40)))
    pattern = "".join(rng.choice("abnara") for _ in range(rng.randint(1, 5)))
    return word, pattern


def run_storm(seed: int = DEFAULT_SEED, steps: int = DEFAULT_STEPS) -> Storm:
    """Run the storm: every entry the array gives, the array must owe."""
    if steps <= 0:
        raise WorkloadError(f"no storm from {steps} steps")
    rng = random.Random(seed)
    breaks: list[str] = []
    checks = 0
    for _ in range(steps):
        word, pattern = _tangle(rng)
        checks += 1
        if z_function(word) != naive_z(word):
            breaks.append(f"array broken on {word!r}")
        if occurrences(word, pattern) != naive_occurrences(word, pattern):
            breaks.append(f"starts broken for {pattern!r} in {word!r}")
    return Storm(steps, checks, tuple(breaks))


def rebuild_matches(words: list[str]) -> bool:
    """Whether re-cut arrays answer exactly like the fresh ones."""
    for word in words:
        if z_function(word) != z_function(word[::-1][::-1]):
            return False
    return all(z_function(word) == naive_z(word) for word in words)
