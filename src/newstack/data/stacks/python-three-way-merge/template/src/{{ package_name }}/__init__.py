"""A three-way merge that names what it could not decide."""

from .change import Change, changes
from .merge import (
    BOTH,
    CONFLICT,
    DIFF3,
    MERGE,
    OURS,
    SAME,
    STYLES,
    THEIRS,
    Chunk,
    MergeError,
    MergeResult,
    merge_files,
    merge_text,
)

__version__ = "0.1.0"

__all__ = [
    "BOTH",
    "CONFLICT",
    "DIFF3",
    "MERGE",
    "OURS",
    "SAME",
    "STYLES",
    "THEIRS",
    "Change",
    "Chunk",
    "MergeError",
    "MergeResult",
    "__version__",
    "changes",
    "merge_files",
    "merge_text",
]
