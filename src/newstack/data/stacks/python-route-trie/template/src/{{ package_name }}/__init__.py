"""Route matching where the walk's order is the rule."""

from .pattern import (
    CATCHALL,
    PARAM,
    STATIC,
    Pattern,
    PatternError,
    Segment,
    parse_pattern,
    split_path,
)
from .router import MATCH, METHODS, NO_MATCH, NOT_ALLOWED, Resolution, Route, Router, RouterError

__version__ = "0.1.0"

__all__ = [
    "CATCHALL",
    "MATCH",
    "METHODS",
    "NOT_ALLOWED",
    "NO_MATCH",
    "PARAM",
    "STATIC",
    "Pattern",
    "PatternError",
    "Resolution",
    "Route",
    "Router",
    "RouterError",
    "Segment",
    "__version__",
    "parse_pattern",
    "split_path",
]
