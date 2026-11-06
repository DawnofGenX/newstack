"""A search tree that is also a heap, and proves it against bisect.

Priorities come from one seeded draw, split and merge are the only
edits: heap order and search order hold after every op of a seeded
storm, `rank` answers what `bisect` answers, and the selftest refuses
to pass when they stop agreeing.
"""

from __future__ import annotations

from .draws import DEFAULT_SEED, MAX_PRIORITY, DrawError, Draws, expected_depth
from .keys import KeyValueError, describe, ensure_key
from .streams import Snapshot, StreamError, load_keys, synthetic, write_keys
from .treap import Edit, Treap, TreapError
from .workload import Replay, WorkloadError, run_workload

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_PRIORITY",
    "DrawError",
    "Draws",
    "Edit",
    "KeyValueError",
    "Replay",
    "Snapshot",
    "StreamError",
    "Treap",
    "TreapError",
    "WorkloadError",
    "__version__",
    "describe",
    "ensure_key",
    "expected_depth",
    "load_keys",
    "run_workload",
    "synthetic",
    "write_keys",
]
