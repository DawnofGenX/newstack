"""Version ranges as a union of intervals."""

from .ranges import Arm, Range, RangeError, intersect, parse_range
from .version import Version, VersionError, compare, parse

__all__ = [
    "Arm",
    "Range",
    "RangeError",
    "Version",
    "VersionError",
    "compare",
    "intersect",
    "parse",
    "parse_range",
]
