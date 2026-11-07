"""Lowercase text, honestly scanned: the table and the scan that checks it.

The automaton seats a pattern so the failure table is always the
naive border count, and every start the scan reports is the naive
scan's start list — overlaps counted, the empty pattern sitting at
every position. The promise is checked, never assumed: the starts
cannot tell a KMP scan from a dumb one.
"""

from __future__ import annotations

from .automaton import (
    AutomatonError,
    KmpAutomaton,
    failure_table,
    scan_starts,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_patterns,
    synthetic,
    write_patterns,
)
from .naive import border_length, naive_count, naive_starts
from .pattern import MAX_PATTERN, PatternError, ensure_pattern

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_PATTERN",
    "AutomatonError",
    "CorpusError",
    "KmpAutomaton",
    "PatternError",
    "Snapshot",
    "__version__",
    "border_length",
    "ensure_pattern",
    "failure_table",
    "load_patterns",
    "naive_count",
    "naive_starts",
    "scan_starts",
    "synthetic",
    "write_patterns",
]
