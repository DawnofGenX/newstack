"""Integer keys, forest-ordered: the heap and the sort that checks it.

The forest ranks integer-keyed items so pop-min replays the plain
`sorted(keys)`, decrease-key drops a tracked item without breaking
heap order (a cascading cut pays the marked-children debt), and
every degree stays under the documented log bound — checked against
the raw-link walk and the audit walk, never assumed. Decrease-key
targets are tracked by the Handle push hands back.
"""

from __future__ import annotations

from .brute import expose, naive_min, naive_sort
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_items,
    synthetic,
    write_items,
)
from .heap import FibonacciHeap, Handle, HeapError, degree_bound
from .keys import MAX_KEY, KeysError, ensure_key

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_KEY",
    "CorpusError",
    "FibonacciHeap",
    "Handle",
    "HeapError",
    "KeysError",
    "Snapshot",
    "__version__",
    "degree_bound",
    "ensure_key",
    "expose",
    "load_items",
    "naive_min",
    "naive_sort",
    "synthetic",
    "write_items",
]
