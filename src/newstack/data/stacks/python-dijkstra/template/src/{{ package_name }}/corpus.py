"""Graphs in, reports out: weighted corpora, generators, snapshots.

One graph per line, tokens spaced apart; blank lines and # comments
are skipped and every other line must pass the parser's gate. The
generator is deterministic from its seed, so a frozen corpus
replays its graphs - weights and all - exactly, in order, forever.
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
    """A deterministic list of small weighted digraphs, tangled and sparse.

    Some generators drop a node's doors shut on purpose: a corpus
    with no unreachable nodes proves nothing about omission.
    """
    if count <= 0:
        raise CorpusError(f"no graphs from {count}")
    rng = random.Random(seed)
    graphs: list = []
    seen: set = set()
    while len(graphs) < count:
        size = rng.randint(2, 12)
        graph = Graph()
        for node in range(size):
            graph.add_node(node)
        for source in range(size):
            if rng.random() < 0.15:
                continue
            for target in range(size):
                if source != target and rng.random() < rng.choice((0.12, 0.25, 0.4)):
                    graph.add_edge(source, target, rng.randint(0, 9))
        if rng.random() < 0.4:
            anchor = rng.randrange(size)
            partner = rng.randrange(size)
            if anchor != partner:
                graph.add_edge(anchor, partner, rng.randint(1, 9))
                graph.add_edge(partner, anchor, rng.randint(1, 9))
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
    """Walk the corpus and answer line by line, reach and farthest cost."""
    from .oracle import relax_map

    lines: list = []
    for graph in graphs:
        costs = relax_map(graph, min(graph.nodes()))
        farthest = max(costs.values()) if costs else 0
        lines.append(
            f"{len(graph)} nodes -> {len(costs)} reached "
            f"farthest {farthest} {graph.to_text()[:36]!r}"
        )
    return lines
