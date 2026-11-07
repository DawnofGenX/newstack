"""Graphs in, reports out: digraph corpora, generators, snapshots.

One graph per line, tokens spaced apart; blank lines and # comments
are skipped and every other line must pass the parser's gate. The
generator is deterministic from its seed and grows a walking chain
first - each new node hangs off one already standing - so the
walker always has a road to walk and the matrix always has a table
to answer.
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


def reaches_all(graph: Graph) -> bool:
    """True when the smallest label walks to every node.

    The generator hangs each new node off one already standing, so
    the root always has a road to every node - the promise a
    generated corpus actually owes, arrows pointing one way.
    """
    nodes = graph.nodes()
    if not nodes:
        return False
    seen = {nodes[0]}
    queue = [nodes[0]]
    while queue:
        for tail, _weight in graph.neighbours(queue.pop()):
            if tail not in seen:
                seen.add(tail)
                queue.append(tail)
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
    """A deterministic list of small weighted digraphs.

    Every graph is a chain walked first - each new node takes an
    arrow from one already standing - so the walker always has a
    road and the table always has pairs to speak. Past sizes stay
    tiny: the walk is a fixed point, on purpose.
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
            graph.add_edge(rng.randrange(node), node, rng.randint(0, 9))
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
    """Walk the corpus and answer line by line, table size and agreement."""
    from .oracle import distance_table
    from .solve import distances

    lines: list = []
    for graph in graphs:
        answered = distances(graph)
        walked = distance_table(graph)
        lines.append(
            f"{len(graph)} nodes -> table {len(answered)} walker {len(walked)} "
            f"equal={answered == walked} {graph.to_text()[:36]!r}"
        )
    return lines
