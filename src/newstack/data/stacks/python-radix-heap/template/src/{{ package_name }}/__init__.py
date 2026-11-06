"""An integer min-heap that never compares keys, and proves it.

Buckets follow the bits: every key sits at its bit-length-from-base
bucket, pop-min reads buckets in order instead of asking which key is
smaller, and the selftest refuses to pass when the drained answer stops
equaling the sorted corpus on monotone and mixed streams alike.
"""

from __future__ import annotations

from .heap import BUCKETS, Edit, HeapError, RadixHeap, bucket_of
from .keys import KeyValueError, describe, ensure_key
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_keys,
    monotone,
    synthetic,
    write_keys,
)
from .workload import Replay, WorkloadError, run_monotone, run_workload

__version__ = "0.1.0"

__all__ = [
    "BUCKETS",
    "DEFAULT_SEED",
    "Edit",
    "HeapError",
    "KeyValueError",
    "RadixHeap",
    "Replay",
    "Snapshot",
    "StreamError",
    "WorkloadError",
    "__version__",
    "bucket_of",
    "describe",
    "ensure_key",
    "load_keys",
    "monotone",
    "run_monotone",
    "run_workload",
    "synthetic",
    "write_keys",
]
