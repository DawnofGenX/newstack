"""Small undirected graphs, honestly spanned: the walker, the enumeration.

spanning_tree(graph) answers the tree's edge set - the same total
the dumb enumeration oracle answers as minimum - tree_cost(graph)
answers its weight, and witness(graph) answers the honest per-edge
record of the sorted walk. The promise is checked, never assumed:
the sorted walk joins fragments and refuses cycles, and a
disconnected graph is named, never spanned.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    is_connected,
    load_graphs,
    report_lines,
    synthetic,
)
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import (
    OracleError,
    min_cost,
    oracle_cost,
    spanning_trees,
    tree_total,
)
from .solve import (
    Fragment,
    Step,
    TreeError,
    audit,
    spanning_tree,
    tree_cost,
    witness,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "CorpusError",
    "Fragment",
    "Graph",
    "GraphError",
    "OracleError",
    "Snapshot",
    "Step",
    "TreeError",
    "__version__",
    "audit",
    "is_connected",
    "load_graphs",
    "min_cost",
    "oracle_cost",
    "parse_graph",
    "report_lines",
    "spanning_tree",
    "spanning_trees",
    "synthetic",
    "tree_cost",
    "tree_total",
    "witness",
]
