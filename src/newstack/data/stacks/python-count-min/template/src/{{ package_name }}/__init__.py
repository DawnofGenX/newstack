"""Counts on a fixed universe: rows of cells, the min that answers.

A count-min sketch over [0, 256): five deterministic multiplicative
rows, an answer that is the min of the rows a key visits, an audit
after every update that the min never dips under the truth, and —
on the shipped corpora, because the rows are bijections the width
can seat alone — answers equal to the ledger exactly.
"""

from __future__ import annotations

from .brute import min_of_rows, true_counts
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_stream,
    synthetic,
    write_stream,
)
from .hashes import DEPTH, MULTIPLIERS, WIDTH, bijective, cell_of
from .keys import MAX_KEY, UNIVERSE, KeysError, ensure_key
from .sketch import CountMinSketch, SketchError

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "DEPTH",
    "MAX_KEY",
    "MULTIPLIERS",
    "UNIVERSE",
    "WIDTH",
    "CorpusError",
    "CountMinSketch",
    "KeysError",
    "SketchError",
    "Snapshot",
    "__version__",
    "bijective",
    "cell_of",
    "ensure_key",
    "load_stream",
    "min_of_rows",
    "synthetic",
    "true_counts",
    "write_stream",
]
