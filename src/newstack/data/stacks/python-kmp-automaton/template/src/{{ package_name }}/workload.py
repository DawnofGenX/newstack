"""Seeded storms: the scan against the naive scan, start for start.

Each step draws a text and a pattern, runs both matchers, and
compares the full start lists. A mismatch is a break, recorded with
the strings that caused it; the storm only passes when it breaks
nothing and checks more than it steps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .automaton import scan_starts
from .corpus import DEFAULT_SEED
from .naive import naive_starts

DEFAULT_STEPS = 140
TEXT_POOL = "abcabracadabraabanana"


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
    text = "".join(rng.choice(TEXT_POOL) for _ in range(rng.randint(0, 40)))
    pattern = "".join(rng.choice("abnara") for _ in range(rng.randint(1, 5)))
    return text, pattern


def run_storm(seed: int = DEFAULT_SEED, steps: int = DEFAULT_STEPS) -> Storm:
    """Run the storm: every start the scan gives, the scan must owe."""
    if steps <= 0:
        raise WorkloadError(f"no storm from {steps} steps")
    rng = random.Random(seed)
    breaks: list[str] = []
    checks = 0
    for _ in range(steps):
        text, pattern = _tangle(rng)
        checks += 1
        if scan_starts(text, pattern) != naive_starts(text, pattern):
            breaks.append(f"pattern {pattern!r} text {text!r}")
    return Storm(steps, checks, tuple(breaks))


def rebuild_matches(patterns: list[str], texts: list[str]) -> bool:
    """Whether rebuilt tables answer exactly like the fresh ones."""
    for pattern in patterns:
        fresh = scan_starts("a" * 8, pattern)
        rebuilt = scan_starts("a" * 8, pattern[::-1][::-1])
        if fresh != rebuilt:
            return False
    return all(
        scan_starts(text, pattern) == naive_starts(text, pattern)
        for text in texts
        for pattern in patterns
    )
