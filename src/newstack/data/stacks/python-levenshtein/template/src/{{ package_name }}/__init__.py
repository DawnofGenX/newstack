"""Unit-cost edit distance over lowercase strings, and the oracle that checks it.

A change costs one letter: insert, delete, and substitute each spend
one, the row walk answers, the bare recursion proves, and the selftest
refuses to pass when a distance stops being symmetric, a detour stops
costing at least as much, or a nearest answer stops equaling the scan.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    load_words,
    synthetic,
    write_words,
)
from .distance import (
    SHIPPED,
    TRIPLES,
    DistanceError,
    distance,
    nearest,
    rank_pairs,
)
from .oracle import ORACLE_LIMIT, oracle_distance
from .words import WordError, ensure_text, ensure_word
from .workload import Replay, WorkloadError, run_storm, shuffle_matches

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "ORACLE_LIMIT",
    "SHIPPED",
    "TRIPLES",
    "CorpusError",
    "DistanceError",
    "Replay",
    "WordError",
    "WorkloadError",
    "__version__",
    "distance",
    "ensure_text",
    "ensure_word",
    "load_words",
    "nearest",
    "oracle_distance",
    "rank_pairs",
    "run_storm",
    "shuffle_matches",
    "synthetic",
    "write_words",
]
