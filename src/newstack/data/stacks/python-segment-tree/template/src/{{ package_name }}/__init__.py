"""A segment tree over an integer array, and the seam it folds through.

Every window answers exactly as the matching slice sums: a pull-up
re-folds the path an edit touched, a query walks the ladder inside a
bit-length bound, and the selftest refuses to pass when the ladder
stops being the truth.
"""

from __future__ import annotations

from .array import (
    DEFAULT_SEED,
    ArrayValueError,
    describe,
    ensure_value,
    load_values,
    synthetic,
    write_values,
)
from .tree import (
    NEUTRAL,
    SegmentError,
    SegmentTree,
    addition,
    minimum,
)
from .workload import STEPS, Replay, WorkloadError, run_bound, run_workload

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "NEUTRAL",
    "STEPS",
    "ArrayValueError",
    "Replay",
    "SegmentError",
    "SegmentTree",
    "WorkloadError",
    "__version__",
    "addition",
    "describe",
    "ensure_value",
    "load_values",
    "minimum",
    "run_bound",
    "run_workload",
    "synthetic",
    "write_values",
]
