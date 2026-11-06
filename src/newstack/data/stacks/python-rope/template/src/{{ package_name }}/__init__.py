"""Texts as trees of chunks: the rope, its corpus, and a CLI that edits."""

from __future__ import annotations

from .corpus import CorpusError, load_text, synthetic
from .rope import Rope, RopeError, Shape

__version__ = "0.1.0"

__all__ = [
    "CorpusError",
    "Rope",
    "RopeError",
    "Shape",
    "__version__",
    "load_text",
    "synthetic",
]
