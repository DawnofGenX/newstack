"""A Bloom filter over ``[0, 256)`` that is only allowed to lie one way.

Add seats a key by raising its k multiplicative rows; ``might_contain``
answers present only when every row is already raised. The promise is
the filter's whole dignity: a key added is *always* answered present —
the shipped audit re-asks every key after every update on the seeded
streams and reports the count — and a yes may only ever be another
key's seating standing in for its own. Removal is refused, not
forgotten: clearing rows erases whoever shares them.
"""

from __future__ import annotations

from .audit import (
    COLLISIONS_AT_DEFAULTS,
    CONFIGS,
    RECHECKS,
    STREAM_SEEDS,
    AuditError,
    Ledger,
    Verdict,
    audit_fixture,
    collision_table,
    estimate_items,
    run_stream,
    shipped_audit,
)
from .bloom import (
    MAX_ROWS,
    MAX_WIDTH,
    MIN_WIDTH,
    ROWS,
    SEED,
    WIDTH,
    Bloom,
    BloomError,
)
from .cli import main
from .hashing import (
    BASE,
    LARGE,
    STEP,
    multiplier,
    row_index,
    rows_for,
)
from .selftest import Report
from .selftest import run as selftest
from .stream import (
    FIXTURE,
    LENGTH,
    Plan,
    StreamError,
    load_fixture,
    stream,
    write_fixture,
)
from .universe import (
    UNIVERSE,
    UniverseError,
    describe,
    ensure_key,
    ensure_seed,
    parse_key,
)

__version__ = "0.1.0"

__all__ = [
    "BASE",
    "COLLISIONS_AT_DEFAULTS",
    "CONFIGS",
    "FIXTURE",
    "LARGE",
    "LENGTH",
    "MAX_ROWS",
    "MAX_WIDTH",
    "MIN_WIDTH",
    "RECHECKS",
    "ROWS",
    "SEED",
    "STEP",
    "STREAM_SEEDS",
    "UNIVERSE",
    "WIDTH",
    "AuditError",
    "Bloom",
    "BloomError",
    "Ledger",
    "Plan",
    "Report",
    "StreamError",
    "UniverseError",
    "Verdict",
    "__version__",
    "audit_fixture",
    "collision_table",
    "describe",
    "ensure_key",
    "ensure_seed",
    "estimate_items",
    "load_fixture",
    "main",
    "multiplier",
    "parse_key",
    "row_index",
    "rows_for",
    "run_stream",
    "selftest",
    "shipped_audit",
    "stream",
    "write_fixture",
]
