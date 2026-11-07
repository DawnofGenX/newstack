"""Lowercase text, honestly counted: the run, the pair, the loop.

encode(text) answers with a pair stream - one (letter, count) for
every run the stepper walks, counts capped at MAX_RUN - and
decode replays each pair letter by letter. The rule every pair
keeps: a run is walked once and answered as a pair. The promise is
checked, never assumed: decode(encode(text)) is the text itself on
every shipped and seeded corpus, and encode answers exactly what
the shipped stepper walks.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    synthetic,
    write_texts,
)
from .naive import (
    naive_decode,
    naive_encode,
    naive_price,
    naive_roundtrip,
)
from .pairs import (
    MAX_RUN,
    Pair,
    PairsError,
    pairs_from_json,
    pairs_to_json,
    walk_runs,
)
from .rle import (
    RunError,
    audit,
    decode,
    encode,
)
from .text import LETTERS, MAX_TEXT, TextError, ensure_text

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "LETTERS",
    "MAX_RUN",
    "MAX_TEXT",
    "CorpusError",
    "Pair",
    "PairsError",
    "RunError",
    "Snapshot",
    "TextError",
    "__version__",
    "audit",
    "decode",
    "encode",
    "ensure_text",
    "load_texts",
    "naive_decode",
    "naive_encode",
    "naive_price",
    "naive_roundtrip",
    "pairs_from_json",
    "pairs_to_json",
    "report_lines",
    "synthetic",
    "walk_runs",
    "write_texts",
]
