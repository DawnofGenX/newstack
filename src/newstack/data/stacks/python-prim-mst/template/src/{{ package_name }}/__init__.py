"""Small undirected graphs, honestly spanned: the grower, the enumeration.

spanning_tree(graph, start) answers the tree's edge set - the same
total the dumb enumeration oracle answers as minimum - and
tree_cost(graph, start) answers its weight. The promise is
checked, never assumed: a node joins the tree once, through the
cheapest crossing edge, and a disconnected graph is named, never
spanned.
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
    write_graphs,
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
    TreeError,
    audit,
    spanning_tree,
    tree_cost,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "CorpusError",
    "Graph",
    "GraphError",
    "OracleError",
    "Snapshot",
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
    "write_graphs",
]
