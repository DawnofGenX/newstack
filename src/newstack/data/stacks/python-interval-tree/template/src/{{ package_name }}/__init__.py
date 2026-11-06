"""Half-open integer spans, a centered interval tree, and the scan that checks it.

The spans carry the semantics, the tree carries the answers, and the scan
carries the truth every answer is compared against.
"""

from __future__ import annotations

from .corpus import CorpusError, load_spans, synthetic, write_spans
from .scan import scan_overlap, scan_stab
from .span import Interval, SpanError
from .tree import IntervalTree, TreeError

__version__ = "0.1.0"

__all__ = [
    "CorpusError",
    "Interval",
    "IntervalTree",
    "SpanError",
    "TreeError",
    "__version__",
    "load_spans",
    "scan_overlap",
    "scan_stab",
    "synthetic",
    "write_spans",
]
