"""Five stories about a bit-array that is only allowed to lie one way.

Every number printed here is computed at run time by the real
modules against the real audit; a story that stops holding fails
the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .audit import (
    COLLISIONS_AT_DEFAULTS,
    CONFIGS,
    estimate_items,
    shipped_audit,
)
from .bloom import ROWS, SEED, WIDTH, Bloom
from .hashing import multiplier
from .stream import Plan, stream

DEMO_WIDTH = 64
DEMO_ROWS = 4
DEMO_SEED = 7
DEMO_STREAM = 7


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The claims the filter makes, each computed fresh."""
    ledger = shipped_audit()
    first = Story(
        "a key the filter was told is never answered absent",
        (
            f"{ledger.checks} re-asks across "
            f"{len(ledger.verdicts)} config/stream pairs, "
            f"{len(ledger.breaks)} breaks"
        ),
        not ledger.breaks,
    )

    liars = sum(len(verdict.false_positives) for verdict in ledger.verdicts)
    second = Story(
        "at the shipped widths no absent key answers present",
        f"{liars} liars across widths "
        f"{', '.join(str(width) for _, width, _, _ in CONFIGS)} — the widths are checked, "
        "not prayed over",
        liars == 0,
    )

    demo = Bloom(DEMO_WIDTH, DEMO_ROWS, DEMO_SEED)
    for key in stream(DEMO_STREAM, 8):
        demo.add(key)
    edge = demo.survey()
    third = Story(
        "the honest edge: a yes can be another key's seating",
        (
            f"{DEMO_WIDTH}-bit array, 8 keys, {len(edge)} absent keys answer "
            f"present ({edge[:3]}...) — collisions only ever answer present"
        ),
        len(edge) > 0 and not demo.audit(),
    )

    plan = Plan.draw(SEED + 1)
    once = Bloom(WIDTH, ROWS, SEED)
    twice = Bloom(WIDTH, ROWS, SEED)
    for key in plan.keys:
        once.add(key)
    for key in stream(plan.seed, plan.length):
        twice.add(key)
    fourth = Story(
        "same seed, same answers, forever",
        (
            f"stream seed {plan.seed} seats {plan.length} keys to {once.bits_set} bits "
            f"both times: {once.bits == twice.bits}"
        ),
        once.bits == twice.bits and once.bits == twice.bits,
    )

    crowded = Bloom(1024, 4, 11)
    for key in stream(7):
        crowded.add(key)
    estimate = estimate_items(crowded)
    fifth = Story(
        "how full is a filter that stores no count",
        (
            f"{crowded.bits_set} of 1024 bits raised after {len(crowded.added)} keys; "
            f"the fill-inversion estimator answers {estimate:.3f} — reported, not hidden"
        ),
        abs(estimate - len(crowded.added)) < 2.0,
    )

    muls = [multiplier(row, SEED) for row in range(ROWS)]
    sixth = Story(
        "the seating is arithmetic, so the edge is countable",
        (
            f"at {WIDTH}x{ROWS} seed {SEED}: {COLLISIONS_AT_DEFAULTS} colliding pairs, "
            f"every multiplier odd: {all(mul & 1 for mul in muls)}"
        ),
        COLLISIONS_AT_DEFAULTS > 0 and all(mul & 1 for mul in muls),
    )
    return [first, second, third, fourth, fifth, sixth]
