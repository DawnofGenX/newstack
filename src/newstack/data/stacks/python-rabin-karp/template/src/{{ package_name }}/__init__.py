"""Lowercase text, honestly scanned: the roll, the check, the starts.

The scanner weighs a window with a documented base and modulus and
rolls it one letter at a time — but a digest is only a question.
Every candidate still walks the letters, so every start the scan
reports is the naive scan's start list, overlaps counted, the empty
pattern sitting at every position. The promise is checked, never
assumed: the starts cannot tell a rolling scan from a dumb one.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_patterns,
    synthetic,
    write_patterns,
)
from .hashing import (
    BASE,
    MODULUS,
    HashError,
    leading_power,
    letter_value,
    roll,
    window_hash,
    windows,
)
from .naive import naive_count, naive_starts
from .pattern import MAX_PATTERN, PatternError, ensure_pattern, ensure_text
from .scanner import RollingScanner, ScannerError, scan_starts

__version__ = "0.1.0"

__all__ = [
    "BASE",
    "DEFAULT_SEED",
    "MAX_PATTERN",
    "MODULUS",
    "CorpusError",
    "HashError",
    "PatternError",
    "RollingScanner",
    "ScannerError",
    "Snapshot",
    "__version__",
    "ensure_pattern",
    "ensure_text",
    "leading_power",
    "letter_value",
    "load_patterns",
    "naive_count",
    "naive_starts",
    "roll",
    "scan_starts",
    "synthetic",
    "window_hash",
    "windows",
    "write_patterns",
]
