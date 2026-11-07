"""Small digraphs, honestly carried: the walker, the cut enumeration.

max_flow(graph, source, sink) answers the value the network carries
- the same least the dumb cut enumeration answers - and
flow_map(graph, source, sink) answers the shipped amount per arc.
The promise is checked, never assumed: flow walks the residual,
never past a bottleneck, and a network with no route answers zero.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    has_route,
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
    cut_capacity,
    cuts,
    least_cut,
    min_cut,
    oracle_value,
)
from .solve import (
    FlowError,
    audit,
    flow_map,
    max_flow,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "CorpusError",
    "FlowError",
    "Graph",
    "GraphError",
    "OracleError",
    "Snapshot",
    "__version__",
    "audit",
    "cut_capacity",
    "cuts",
    "flow_map",
    "has_route",
    "least_cut",
    "load_graphs",
    "max_flow",
    "min_cut",
    "oracle_value",
    "parse_graph",
    "report_lines",
    "synthetic",
    "write_graphs",
]
