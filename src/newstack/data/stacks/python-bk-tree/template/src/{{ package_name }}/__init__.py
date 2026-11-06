"""A Burkhard-Keller tree over edit distance, with the pruning kept honest."""

from __future__ import annotations

from .corpus import CorpusError, dedupe, load_words, synthetic
from .distance import (
    DistanceError,
    Measurement,
    Violation,
    levenshtein,
    measurement,
    osa,
    triangle_violation,
)
from .tree import BKTree, Hit, Search, TreeError, search_by

__version__ = "0.1.0"

__all__ = [
    "BKTree",
    "CorpusError",
    "DistanceError",
    "Hit",
    "Measurement",
    "Search",
    "TreeError",
    "Violation",
    "__version__",
    "dedupe",
    "levenshtein",
    "load_words",
    "measurement",
    "osa",
    "search_by",
    "synthetic",
    "triangle_violation",
]
