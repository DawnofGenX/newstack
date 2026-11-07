"""The shipped audit: a falsifiable core, run key by key.

The filter makes exactly one promise — a key it was told is always
answered present — and this module holds it to that promise the
only way that counts: after *every* update on every seeded stream,
every key added so far is re-asked. Zero false negatives is not a
theorem here, it is a finished count: RECHECKS re-asks across the
config-and-stream pairs of ``CONFIGS``, none lying. The survey then
answers the other half honestly: at the shipped widths no absent key
answers present, list in hand — because a collision can only ever
lie toward *present*, never away.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .bloom import ROWS, SEED, WIDTH, Bloom
from .hashing import rows_for
from .stream import (
    LENGTH,
    Plan,
    StreamError,
    load_fixture,
    stream,
)
from .universe import UNIVERSE

# (name, width, rows, seat seed). Every pair below answers present to
# zero absent keys on every shipped stream — a checked fact, not a
# hope; seat seed 42 was rejected at 1024x4 for lying about key 204.
CONFIGS: tuple[tuple[str, int, int, int], ...] = (
    ("wide-1024", 1024, 4, 11),
    ("wide-1024-alt", 1024, 4, 17),
    ("wide-2048", 2048, 4, 11),
)
STREAM_SEEDS: tuple[int, ...] = (7, 13, 42, 101, 2026)
RECHECKS = len(CONFIGS) * len(STREAM_SEEDS) * sum(range(1, LENGTH + 1))

# 369 unordered pairs of the universe share at least one row at the
# default seating: the raw edge a survey counts when it lies present.
COLLISIONS_AT_DEFAULTS = 369


class AuditError(ValueError):
    """An audit input cannot be used as given."""


@dataclass(frozen=True)
class Verdict:
    """One config, one stream, the counts that settle it."""

    config: str
    seed: int
    updates: int
    rechecks: int
    false_negatives: tuple[int, ...]
    false_positives: tuple[int, ...]

    @property
    def clean(self) -> bool:
        return not self.false_negatives and not self.false_positives


@dataclass
class Ledger:
    """Every verdict the shipped audit has handed down."""

    verdicts: list[Verdict] = field(default_factory=list)

    @property
    def checks(self) -> int:
        return sum(verdict.rechecks for verdict in self.verdicts)

    @property
    def breaks(self) -> list[str]:
        broken: list[str] = []
        for verdict in self.verdicts:
            for key in verdict.false_negatives:
                broken.append(f"{verdict.config}/{verdict.seed}: {key} reads absent")
            for key in verdict.false_positives:
                broken.append(f"{verdict.config}/{verdict.seed}: {key} lied present")
        return broken


def run_stream(config: str, width: int, rows: int, seat_seed: int, plan: Plan) -> Verdict:
    """Add the plan's keys one by one, re-asking every key after each add."""
    if plan.length < 2:
        raise AuditError(f"plan of {plan.length} keys audits nothing")
    bloom = Bloom(width=width, rows=rows, seed=seat_seed)
    rechecks = 0
    misses: list[int] = []
    for key in plan.keys:
        bloom.add(key)
        for seated in bloom.added:
            rechecks += 1
            if not bloom.might_contain(seated):
                misses.append(seated)
    return Verdict(
        config=config,
        seed=plan.seed,
        updates=plan.length,
        rechecks=rechecks,
        false_negatives=tuple(misses),
        false_positives=tuple(bloom.survey()),
    )


def shipped_audit() -> Ledger:
    """Every shipped config against every shipped stream: the whole proof."""
    ledger = Ledger()
    for config, width, rows, seat_seed in CONFIGS:
        for seed in STREAM_SEEDS:
            plan = Plan(seed=seed, keys=stream(seed))
            ledger.verdicts.append(run_stream(config, width, rows, seat_seed, plan))
    return ledger


def audit_fixture(path: str) -> Ledger:
    """The frozen streams through the default shipped shape."""
    try:
        plans = load_fixture(path)
    except (StreamError, OSError) as unreadable:
        raise AuditError(f"fixture unusable: {unreadable}") from None
    ledger = Ledger()
    for plan in plans:
        ledger.verdicts.append(run_stream("fixture", WIDTH, ROWS, SEED, plan))
    return ledger


def collision_table(
    width: int = WIDTH, rows: int = ROWS, seat_seed: int = SEED
) -> int:
    """Pairs of universe keys sharing at least one row: the raw edge."""
    seats = {key: set(rows_for(key, width, rows, seat_seed)) for key in range(UNIVERSE)}
    return sum(
        1
        for first in range(UNIVERSE)
        for second in range(first + 1, UNIVERSE)
        if seats[first] & seats[second]
    )


def estimate_items(bloom: Bloom) -> float:
    """Keys implied by the fill: -(m/k)·ln(cleared/m), the classic curve.

    The filter stores no count and answers no capacity, so the only
    honest answer about "how full" is this inversion of the fill; it
    runs to the universe size once every bit is raised.
    """
    cleared = bloom.width - bloom.bits_set
    if cleared <= 0:
        return float(UNIVERSE)
    return -bloom.width / bloom.rows * math.log(cleared / bloom.width)
