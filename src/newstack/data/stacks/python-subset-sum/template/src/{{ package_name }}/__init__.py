"""Subset sum over small nonnegative integers."""

from __future__ import annotations

from .solve import (
    MAX_TARGET,
    MAX_VALUE,
    MAX_VALUES,
    SubsetSumError,
    audit,
    solve,
    witness,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_TARGET",
    "MAX_VALUE",
    "MAX_VALUES",
    "SubsetSumError",
    "audit",
    "solve",
    "witness",
]
