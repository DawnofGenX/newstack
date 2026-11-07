"""Seeded storms: the coder against its own loop, text after text.

Each step draws a repetitive text, compresses it, replays the
stream, and compares the answer with the letters it was handed. A
mismatch is a break, recorded with the text that caused it; the
storm only passes when it breaks nothing and checks more than it
steps.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .coder import audit, compress, decompress
from .corpus import DEFAULT_SEED, synthetic
from .tokens import (
    tokens_from_json,
    tokens_to_json,
)

DEFAULT_STEPS = 140


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


def _tangle(rng: random.Random) -> str:
    stem = "".join(rng.choice("abra") for _ in range(rng.randint(1, 6)))
    return stem * rng.randint(1, 10)


def run_storm(seed: int = DEFAULT_SEED, steps: int = DEFAULT_STEPS) -> Storm:
    """Run the storm: every text compressed, the loop must close."""
    if steps <= 0:
        raise WorkloadError(f"no storm from {steps} steps")
    rng = random.Random(seed)
    breaks: list[str] = []
    checks = 0
    for _ in range(steps):
        text = _tangle(rng)
        tokens = compress(text)
        checks += 1
        if decompress(tokens) != text:
            breaks.append(f"{text!r} did not survive the loop")
        checks += 1
        if audit(tokens):
            breaks.append(f"{text!r} quoted beyond the window")
        checks += 1
        if tokens_from_json(tokens_to_json(tokens)) != tokens:
            breaks.append(f"{text!r} lost a token through JSON")
        if stem_repeats(text) >= 3 and len(tokens) >= len(text):
            breaks.append(f"{text!r} a repeat and the coder never blinked")
    return Storm(steps, checks, tuple(breaks))


def stem_repeats(text: str) -> int:
    """How many times the shortest stem spells this text."""
    if not text:
        return 0
    for size in range(1, len(text) + 1):
        if len(text) % size == 0 and text[:size] * (len(text) // size) == text:
            return len(text) // size
    return 1


def honest_streams(count: int = 24, seed: int = DEFAULT_SEED) -> bool:
    """Every stream of a seeded corpus audits silent, text after text."""
    return all(audit(compress(text)) == [] for text in synthetic(count, seed=seed))
