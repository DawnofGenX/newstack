"""A sorted map that balances on coin flips, and proves it against bisect.

Heights come from one seeded generator, link widths come from the map's
own arithmetic: `rank` and `select` answer what `bisect` answers, at
the cost of one walk, and the selftest refuses to pass when they stop
agreeing.
"""

from __future__ import annotations

from .coins import (
    DEFAULT_SEED,
    MAX_LEVEL,
    CoinToss,
    CoinTossError,
    LevelPlan,
    expected_level,
    level_budget,
)
from .keys import SkipKeyValueError, describe, ensure_key
from .map import Edit, SkipList, SkipListError, Walk
from .stack import (
    CorpusError,
    Snapshot,
    load_pairs,
    synthetic,
    write_pairs,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LEVEL",
    "CoinToss",
    "CoinTossError",
    "CorpusError",
    "Edit",
    "LevelPlan",
    "SkipKeyValueError",
    "SkipList",
    "SkipListError",
    "Snapshot",
    "Walk",
    "__version__",
    "describe",
    "ensure_key",
    "expected_level",
    "level_budget",
    "load_pairs",
    "synthetic",
    "write_pairs",
]
