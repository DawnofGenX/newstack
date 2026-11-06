"""Keyed B-trees, a page file, and a corpus that all three can read.

The tree keeps keys in balance, the page file freezes one, and the corpus
feeds the stories that prove both.
"""

from __future__ import annotations

from .btree import BTree, BTreeError, NodeShape
from .corpus import CorpusError, load_keys, synthetic
from .page import PageError, PageReport, read_page, write_page

__version__ = "0.1.0"

__all__ = [
    "BTree",
    "BTreeError",
    "CorpusError",
    "NodeShape",
    "PageError",
    "PageReport",
    "__version__",
    "load_keys",
    "read_page",
    "synthetic",
    "write_page",
]
