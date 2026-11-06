"""A regular expression engine with two machines and no backtracking at run time."""

from __future__ import annotations

from .dfa import Dfa, agreement, determinize
from .match import Match, full, search
from .nfa import Nfa, compile_node, compile_text
from .syntax import PatternError, parse

__version__ = "0.1.0"

__all__ = [
    "Dfa",
    "Match",
    "Nfa",
    "PatternError",
    "__version__",
    "agreement",
    "compile_node",
    "compile_text",
    "determinize",
    "full",
    "parse",
    "search",
]
