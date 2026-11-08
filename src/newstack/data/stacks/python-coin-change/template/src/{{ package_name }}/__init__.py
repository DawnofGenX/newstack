"""Minimum coins to make an amount from unlimited denominations."""

from __future__ import annotations

from .solve import (
    MAX_AMOUNT,
    MAX_COINS,
    MAX_DENOM,
    CoinChangeError,
    audit,
    solve,
    witness,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_AMOUNT",
    "MAX_COINS",
    "MAX_DENOM",
    "CoinChangeError",
    "audit",
    "solve",
    "witness",
]
