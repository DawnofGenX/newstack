"""Graphs in, reports out: connected corpora, generators, snapshots.

One graph per line, tokens spaced apart; blank lines and # comments
are skipped and every other line must pass the parser's gate. The
generator is deterministic from its seed and grows every graph
connected on purpose - a spanning tree needs one piece to span,
and a corpus of connected graphs is what the oracle can enumerate.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .graph import Graph, GraphError, parse_graph

DEFAULT_SEED = 20261107


class CorpusError(GraphError):
    """A corpus cannot be read, written, generated, or replayed."""

    __slots__ = ()


def is_connected(graph: Graph) -> bool:
    """True when every node walks to every other along the edges."""
    nodes = graph.nodes()
    if not nodes:
        return False
    seen = {nodes[0]}
    queue = [nodes[0]]
    while queue:
        for neighbour, _weight in graph.neighbours(queue.pop()):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return len(seen) == len(nodes)


class Snapshot:
    """A frozen corpus and the seed that owes it."""

    __slots__ = ("lines", "seed")

    def __init__(self, lines: tuple, seed: int) -> None:
        self.lines = lines
        self.seed = seed

    def dumps(self) -> str:
        return json.dumps({"seed": self.seed, "graphs": list(self.lines)})

    @classmethod
    def loads(cls, payload: str) -> Snapshot:
        try:
            record = json.loads(payload)
            return cls(tuple(record["graphs"]), int(record["seed"]))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as failure:
            raise CorpusError(f"half a snapshot: {failure}") from failure

    def graphs(self) -> list:
        try:
            return [parse_graph(line) for line in self.lines]
        except GraphError as failure:
            raise CorpusError(f"a snapshot line broke: {failure}") from failure


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list:
    """A deterministic list of small connected weighted graphs.

    Every graph is a span walked first - each new node hangs off a
    node already standing - so the grower always has a tree to
    grow and the oracle always has trees to enumerate. Past sizes
    stay tiny: the enumeration is complete, on purpose.
    """
    if count <= 0:
        raise CorpusError(f"no graphs from {count}")
    rng = random.Random(seed)
    graphs: list = []
    seen: set = set()
    while len(graphs) < count:
        size = rng.randint(2, 8)
        graph = Graph()
        for node in range(size):
            graph.add_node(node)
        for node in range(1, size):
            graph.add_edge(node, rng.randrange(node), rng.randint(0, 9))
        for _ in range(rng.randint(0, size)):
            a = rng.randrange(size)
            b = rng.randrange(size)
            if a != b:
                graph.add_edge(a, b, rng.randint(0, 9))
        text = graph.to_text()
        if text in seen:
            continue
        seen.add(text)
        graphs.append(graph)
    return graphs


def load_graphs(path: str) -> list:
    """One graph per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as failure:
        raise CorpusError(f"no such corpus: {path}") from failure
    graphs: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            graphs.append(parse_graph(stripped))
        except GraphError as failure:
            raise CorpusError(f"the corpus holds {stripped!r}, no graph: {failure}") from failure
    if not graphs:
        raise CorpusError(f"{path} names no graphs")
    return graphs


def write_graphs(graphs: list, path: str) -> None:
    """Write a corpus, one graph per line, ended by a newline."""
    try:
        Path(path).write_text(
            "\n".join(graph.to_text() for graph in graphs) + "\n",
            encoding="utf-8",
        )
    except OSError as failure:
        raise CorpusError(f"cannot write {path}: {failure}") from failure


def report_lines(graphs: list) -> list:
    """Walk the corpus and answer line by line, tree cost and oracle cost."""
    from .oracle import min_cost
    from .solve import tree_cost

    lines: list = []
    for graph in graphs:
        grown = tree_cost(graph, min(graph.nodes()))
        least = min_cost(graph)
        lines.append(
            f"{len(graph)} nodes -> tree {grown} oracle {least} "
            f"equal={grown == least} {graph.to_text()[:36]!r}"
        )
    return lines
