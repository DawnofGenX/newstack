"""Sorted suffix starts of a text, and the scan that checks them.

A suffix is the text from one letter to the end: the table seats those
starts in the order a plain slice-sort would answer, rank doubling
reaches that order without the slicing, and the selftest refuses to
pass when an order stops equaling the sort or a count stops equaling
the scan on seeded text.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    synthetic,
    write_texts,
)
from .scan import scan_array, scan_count, scan_lcp_array, scan_lcp_pair, scan_lrs
from .suffix import SuffixArray, SuffixError, build
from .text import TextError, ensure_pattern, ensure_text

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "CorpusError",
    "Snapshot",
    "SuffixArray",
    "SuffixError",
    "TextError",
    "__version__",
    "build",
    "ensure_pattern",
    "ensure_text",
    "load_texts",
    "scan_array",
    "scan_count",
    "scan_lcp_array",
    "scan_lcp_pair",
    "scan_lrs",
    "synthetic",
    "write_texts",
]
