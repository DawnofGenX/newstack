"""Aho-Corasick automata, a naive reference, and corpora that prove both.

The automaton sweeps a text once; the naive scanner walks it per pattern;
the corpora feed the stories that prove the two answers are one answer.
"""

from __future__ import annotations

from .automaton import AhoCorasick, AhoCorasickError, Hit, Sweep
from .corpus import CorpusError, load_patterns, load_text, prose, random_text
from .naive import NaiveReport, naive_sweep

__version__ = "0.1.0"

__all__ = [
    "AhoCorasick",
    "AhoCorasickError",
    "CorpusError",
    "Hit",
    "NaiveReport",
    "Sweep",
    "__version__",
    "load_patterns",
    "load_text",
    "naive_sweep",
    "prose",
    "random_text",
]
