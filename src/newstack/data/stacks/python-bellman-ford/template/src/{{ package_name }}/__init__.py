"""Small weighted digraphs, honestly walked: the rounds, the count, the cycle.

distances(graph, source) answers the shortest-path map - the same map
the walk-counting oracle answers - and negative_cycle(graph, source)
names the cycle when a walk never settles. The promise is checked,
never assumed: no cheaper walk survives a settled edge, on every
graph the corpora hold.
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
from .cycle import negative_cycle
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    MAX_WEIGHT,
    UNREACHED,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import oracle_distances, oracle_negative
from .walk import (
    WalkError,
    audit,
    distances,
    settled,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "MAX_WEIGHT",
    "UNREACHED",
    "CorpusError",
    "Graph",
    "GraphError",
    "Snapshot",
    "WalkError",
    "__version__",
    "audit",
    "distances",
    "load_graphs",
    "negative_cycle",
    "oracle_distances",
    "oracle_negative",
    "parse_graph",
    "report_lines",
    "settled",
    "synthetic",
    "write_graphs",
]
