"""Small digraphs, honestly walked: the matrix, the walker.

distances(graph) answers the all-pairs table - the same pairs and
costs the walking oracle answers - and worst_hop(graph) answers the
most distant reachable pair. The promise is checked, never assumed:
the table is the walker's table, pair for pair, a diagonal at zero,
an unreached pair omitted, and one more sweep changes nothing.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_graphs,
    reaches_all,
    report_lines,
    synthetic,
    write_graphs,
)
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    hop,
    parse_graph,
)
from .oracle import (
    MAX_SWEEPS,
    OracleError,
    distance_table,
    oracle_table,
    walk_from,
)
from .solve import (
    TableError,
    audit,
    distances,
    restated,
    worst_hop,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "MAX_SWEEPS",
    "CorpusError",
    "Graph",
    "GraphError",
    "OracleError",
    "Snapshot",
    "TableError",
    "__version__",
    "audit",
    "distance_table",
    "distances",
    "hop",
    "load_graphs",
    "oracle_table",
    "parse_graph",
    "reaches_all",
    "report_lines",
    "restated",
    "synthetic",
    "walk_from",
    "worst_hop",
    "write_graphs",
]
