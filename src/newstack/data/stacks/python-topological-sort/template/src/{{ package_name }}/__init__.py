"""Small digraphs, honestly ordered: the order, the block, the picker.

order(graph) lists every node exactly once, predecessors-first - the
same sequence the naive picker answers - and cycle(graph) names the
block honestly when a cycle blocks the listing. The promise is
checked, never assumed: a node is released only when its last
predecessor has gone, and the same graph answers the same sequence.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    TANGLES,
    CorpusError,
    Snapshot,
    load_graphs,
    report_lines,
    synthetic,
    tangles,
    write_graphs,
)
from .cycle import cycle
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import naive_order
from .order import (
    OrderError,
    block,
    order,
    validate,
)

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_LABEL",
    "MAX_NODES",
    "TANGLES",
    "CorpusError",
    "Graph",
    "GraphError",
    "OrderError",
    "Snapshot",
    "__version__",
    "block",
    "cycle",
    "load_graphs",
    "naive_order",
    "order",
    "parse_graph",
    "report_lines",
    "synthetic",
    "tangles",
    "validate",
    "write_graphs",
]
