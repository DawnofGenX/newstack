"""A mergeable integer min-heap of binomial trees, and proves it.

The forest keeps one tree per rank: a tree of rank k holds exactly
2^k keys, the ranks standing present are the bit pattern of the
count, and meld unions two forests -- the answer plain heaps refuse.
The selftest refuses to pass when one claim stops holding.
"""

from __future__ import annotations

from .heap import (
    MAX_RANK,
    BinomialHeap,
    Edit,
    HeapError,
    Tree,
    link,
    ranks_of,
)
from .keys import KeyValueError, bits, describe, ensure_key
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_keys,
    monotone,
    synthetic,
    write_keys,
)
from .workload import Replay, WorkloadError, run_meld, run_monotone, run_workload

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_RANK",
    "BinomialHeap",
    "Edit",
    "HeapError",
    "KeyValueError",
    "Replay",
    "Snapshot",
    "StreamError",
    "Tree",
    "WorkloadError",
    "__version__",
    "bits",
    "describe",
    "ensure_key",
    "link",
    "load_keys",
    "monotone",
    "ranks_of",
    "run_meld",
    "run_monotone",
    "run_workload",
    "synthetic",
    "write_keys",
]
