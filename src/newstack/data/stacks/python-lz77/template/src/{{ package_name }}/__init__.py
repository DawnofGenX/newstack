"""Lowercase text, honestly coded: the window, the quote, the loop.

compress(text) answers with a token stream — literals and
back-references into the sliding window — and decompress replays
that stream letter by letter. The rule every token keeps: the
sliding window never quotes a letter it has never emitted. The
promise is checked, never assumed: the loop closes on every
shipped and seeded corpus, and a repeat never costs more tokens
than letters.
"""

from __future__ import annotations

from .coder import (
    MIN_MATCH,
    CoderError,
    audit,
    compress,
    decompress,
)
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
    naive_emit,
    naive_json_roundtrip,
    naive_read,
    naive_roundtrip,
    naive_size,
)
from .text import LETTERS, MAX_TEXT, TextError, ensure_text
from .tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
    Token,
    TokenError,
    tokens_from_json,
    tokens_to_json,
)
from .workload import Storm, WorkloadError, run_storm

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "LETTERS",
    "MAX_MATCH",
    "MAX_TEXT",
    "MAX_WINDOW",
    "MIN_MATCH",
    "BackRef",
    "CoderError",
    "CorpusError",
    "Literal",
    "Snapshot",
    "Storm",
    "TextError",
    "Token",
    "TokenError",
    "WorkloadError",
    "__version__",
    "audit",
    "compress",
    "decompress",
    "ensure_text",
    "load_texts",
    "naive_emit",
    "naive_json_roundtrip",
    "naive_read",
    "naive_roundtrip",
    "naive_size",
    "report_lines",
    "run_storm",
    "synthetic",
    "tokens_from_json",
    "tokens_to_json",
    "write_texts",
]
