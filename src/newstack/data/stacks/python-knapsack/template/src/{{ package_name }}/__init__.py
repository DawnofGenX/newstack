"""0/1 knapsack over small integer weights and values."""

from __future__ import annotations

from .solve import (
    MAX_CAPACITY,
    MAX_ITEMS,
    MAX_VALUE,
    MAX_WEIGHT,
    KnapsackError,
    audit,
    solve,
    witness,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_CAPACITY",
    "MAX_ITEMS",
    "MAX_VALUE",
    "MAX_WEIGHT",
    "KnapsackError",
    "audit",
    "solve",
    "witness",
]
