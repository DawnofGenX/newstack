"""Small weighted digraphs, honestly routed: the walker, the fixed point.

distances(graph, source) answers the cheapest cost to every reached
node - the same map the dumb relaxation oracle answers - and
path(graph, source, target) answers the cheapest route. The promise
is checked, never assumed: a node is settled only when no edge can
lower its cost, and unreachable nodes are omitted from every map.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
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
    oracle_distances,
    relax_map,
)
from .solve import (
    RouteError,
    audit,
    distances,
    path,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "CorpusError",
    "Graph",
    "GraphError",
    "RouteError",
    "Snapshot",
    "__version__",
    "audit",
    "distances",
    "load_graphs",
    "oracle_distances",
    "parse_graph",
    "path",
    "relax_map",
    "report_lines",
    "synthetic",
    "write_graphs",
]
