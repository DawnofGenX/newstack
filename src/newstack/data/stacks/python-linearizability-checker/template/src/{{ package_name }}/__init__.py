"""Linearizability of a register history: a verdict, a witness, and a smallest core."""

from .check import Outcome, brute_force, check, is_minimal, shrink
from .history import History, HistoryError, Operation, parse_lines

__version__ = "0.1.0"
__all__ = [
    "History",
    "HistoryError",
    "Operation",
    "Outcome",
    "__version__",
    "brute_force",
    "check",
    "is_minimal",
    "parse_lines",
    "shrink",
]
