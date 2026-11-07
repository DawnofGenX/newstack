"""Small digraphs, honestly partitioned: the walk, the oracle, the DAG.

partition(graph) answers the strongly-connected components - the
same partition the dumb reachability oracle answers - and
condense(graph) answers the DAG those components fold to. The
promise is checked, never assumed: two nodes share a component only
when each reaches the other, on every graph the corpora hold.
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
from .cycle import has_cycle
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import oracle_partition, reach
from .scc import (
    PartitionError,
    audit,
    condense,
    partition,
    strong_components,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "CorpusError",
    "Graph",
    "GraphError",
    "PartitionError",
    "Snapshot",
    "__version__",
    "audit",
    "condense",
    "has_cycle",
    "load_graphs",
    "oracle_partition",
    "parse_graph",
    "partition",
    "reach",
    "report_lines",
    "strong_components",
    "synthetic",
    "write_graphs",
]
