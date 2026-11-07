"""Integer elements, one name per component, and a shape that proves it.

The forest keeps its promises in the open: two elements share a
component exactly when their walks land on one name, links point at
roots so depth stays logarithmic, and a render from (element, root)
pairs rebuilds the same partition. Deletions are out of scope.
"""

from __future__ import annotations

from .forest import Shape, UnionFind, UnionFindError
from .pairs import PairError, load_pairs, synthetic

__version__ = "0.1.0"

__all__ = [
    "PairError",
    "Shape",
    "UnionFind",
    "UnionFindError",
    "__version__",
    "load_pairs",
    "synthetic",
]
