"""Canonical Huffman coding over lowercase letters, honestly checked.

build_tree(frequencies) answers with a deterministic ladder — the
two cheapest first, ties falling alphabetically; code_table
deals its depths into canonical bit strings so a decoder never
asks for the tree. encode(text) spends each letter its word and
decode(bits, table) walks the table alone: the product is the
loop, decode(encode(t)) is t on every shipped and seeded corpus,
and no code a coder ships is ever a prefix of another.
"""

from __future__ import annotations

from .coder import (
    CoderError,
    decode,
    encode,
    honest,
    size_report,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    stream_json,
    synthetic,
    write_texts,
)
from .demo import Story, stories
from .freq import (
    Frequency,
    FrequencyError,
    ensure_frequencies,
    tally,
)
from .table import (
    CodeTable,
    TableError,
    audit,
    code_table,
    deal,
)
from .text import LETTERS, MAX_TEXT, TextError, ensure_text
from .tree import (
    Branch,
    Leaf,
    Node,
    TreeError,
    build_tree,
    depths,
    height,
    walk,
    walk_table_agreement,
)
from .workload import Storm, WorkloadError, run_storm

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "LETTERS",
    "MAX_TEXT",
    "Branch",
    "CodeTable",
    "CoderError",
    "CorpusError",
    "Frequency",
    "FrequencyError",
    "Leaf",
    "Node",
    "Snapshot",
    "Storm",
    "Story",
    "TableError",
    "TextError",
    "TreeError",
    "WorkloadError",
    "__version__",
    "audit",
    "build_tree",
    "code_table",
    "deal",
    "decode",
    "depths",
    "encode",
    "ensure_frequencies",
    "ensure_text",
    "height",
    "honest",
    "load_texts",
    "report_lines",
    "run_storm",
    "size_report",
    "stories",
    "stream_json",
    "synthetic",
    "tally",
    "walk",
    "walk_table_agreement",
    "write_texts",
]
