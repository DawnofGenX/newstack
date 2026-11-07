"""Integer values, fixed slots: the ring and the deque that checks it.

A ring buffer seats integer values in a closed set of slots, the
cursor stays inside `[0, capacity)`, the drain equals the fixed-`maxlen`
deque exactly under the drop-oldest policy, and the logical contents
are recomputed from `(head, count)` after every operation — checked
against the reference, the cursor bounds, and the audit, never assumed.
"""

from __future__ import annotations

from .brute import drop_oldest_view, reference_drain, storm_reference
from .corpus import DEFAULT_SEED, CorpusError, Snapshot, load_values, synthetic
from .ring import RingBuffer, RingError
from .storm import StormError, drain_matches, run_storm, storm_matches
from .values import MAX_VALUE, ValuesError, ensure_value

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_VALUE",
    "CorpusError",
    "RingBuffer",
    "RingError",
    "Snapshot",
    "StormError",
    "ValuesError",
    "__version__",
    "drain_matches",
    "drop_oldest_view",
    "ensure_value",
    "load_values",
    "reference_drain",
    "run_storm",
    "storm_matches",
    "storm_reference",
    "synthetic",
]
