"""Seats in [0, 256): a van Emde Boas tree and the scans that check it.

The tree seeks successors and predecessors through cluster
arithmetic; the shipped scans answer the same questions by walking a
sorted list. Every answer the tree gives must equal the scan's, on
every seeded workload, checked never assumed.
"""

from __future__ import annotations

from .brute import (
    brute_sort,
    scan_member,
    scan_predecessor,
    scan_successor,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, UNIVERSE, KeysError, ensure_key
from .tree import TreeError, VanEmdeTree

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_KEY",
    "UNIVERSE",
    "CorpusError",
    "KeysError",
    "Snapshot",
    "TreeError",
    "VanEmdeTree",
    "__version__",
    "brute_sort",
    "ensure_key",
    "load_keys",
    "scan_member",
    "scan_predecessor",
    "scan_successor",
    "synthetic",
    "write_keys",
]
