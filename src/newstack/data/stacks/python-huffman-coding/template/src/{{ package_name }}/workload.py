"""Seeded storms: the coder against its own loop, text after text.

Each step draws a skewed lowercase text, prices it, replays the
bits through the table, and walks the ladder against the table.
A mismatch is a break, recorded with the text that caused it; the
storm only passes when it breaks nothing and checks more than it
steps.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from .coder import decode, encode
from .corpus import DEFAULT_SEED, synthetic
from .freq import tally
from .table import CodeTable, audit, code_table
from .tree import (
    build_tree,
    walk_table_agreement,
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
    pool = "abrna"[: rng.randint(2, 5)]
    weights = [pool[0]] * rng.randint(1, 5) + list(pool)
    return "".join(rng.choice(weights) for _ in range(rng.randint(6, 48)))


def run_storm(seed: int = DEFAULT_SEED, steps: int = DEFAULT_STEPS) -> Storm:
    """Run the storm: every text coded, the loop must close on all."""
    if steps <= 0:
        raise WorkloadError(f"no storm from {steps} steps")
    rng = random.Random(seed)
    breaks: list[str] = []
    checks = 0
    for _ in range(steps):
        text = _tangle(rng)
        book = code_table(tally(text))
        bits = encode(text, book)
        checks += 1
        if decode(bits, book) != text:
            breaks.append(f"{text!r} did not survive the loop")
        checks += 1
        if audit(book):
            breaks.append(f"{text!r} shipped a prefix of another code")
        checks += 1
        ladder = build_tree(tally(text))
        checks += 1
        if not walk_table_agreement(ladder, book):
            breaks.append(f"{text!r}: ladder and table disagree")
        if len(bits) >= len(text) * 8:
            breaks.append(f"{text!r} a skewed text and the coder never blinked")
        wire = json.loads(json.dumps({"bits": bits, "codes": dict(book.codes)}))
        if decode(wire["bits"], CodeTable(dict(wire["codes"]))) != text:
            breaks.append(f"{text!r} lost the loop through JSON")
    return Storm(steps, checks, tuple(breaks))


def honest_streams(count: int = 24, seed: int = DEFAULT_SEED) -> bool:
    """Every table of a seeded corpus audits silent, text after text."""
    return all(audit(code_table(tally(text))) == [] for text in synthetic(count, seed=seed))
