"""A string-keyed trie over lowercase words, and the scan that checks it.

A word ends where it is whole: the branches carry letters, the nodes
carry words, and the selftest refuses to pass when a membership answer
stops equaling a set's or a prefix listing stops equaling the scan.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_words,
    synthetic,
    write_words,
)
from .scan import scan_has, scan_lcp, scan_prefix
from .trie import PrefixTrie, TrieError
from .words import WordError, ensure_prefix, ensure_word
from .workload import Replay, WorkloadError, rebuild_matches, run_storm

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "CorpusError",
    "PrefixTrie",
    "Replay",
    "Snapshot",
    "TrieError",
    "WordError",
    "WorkloadError",
    "__version__",
    "ensure_prefix",
    "ensure_word",
    "load_words",
    "rebuild_matches",
    "run_storm",
    "scan_has",
    "scan_lcp",
    "scan_prefix",
    "synthetic",
    "write_words",
]
