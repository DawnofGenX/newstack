"""Read an ignore file the way git reads it, and say why."""

from .matcher import Matcher, PathError, Verdict
from .pattern import PatternError, Rule, parse_rule, parse_rules

__all__ = [
    "Matcher",
    "PathError",
    "PatternError",
    "Rule",
    "Verdict",
    "parse_rule",
    "parse_rules",
]
__version__ = "0.1.0"
