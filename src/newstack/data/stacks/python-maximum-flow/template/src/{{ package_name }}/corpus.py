"""Networks in, reports out: corpora, generators, snapshots.

One network per line, tokens spaced apart; blank lines and #
comments are skipped and every other line must pass the parser's
gate. The report walks every network from its lowest label to its
highest - the fixture convention for a designated source and sink
- and answers flow and cut side by side. The generator is
deterministic from its seed and ships arcs upward only, so the
lowest label always feeds the highest through something.
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


def has_route(graph: Graph, source: int, sink: int) -> bool:
    """True when some walk of arcs runs source to sink."""
    seen = {source}
    queue = [source]
    while queue:
        for neighbour, _room in graph.out_arcs(queue.pop()):
            if neighbour == sink:
                return True
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return sink in seen


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
    """A deterministic list of small directed capacity networks.

    Arcs run upward only - every arc leaves a lower label for a
    higher one - so the lowest label is always a legal source, the
    highest always a legal sink, and the pair never doubles as two
    channels between one couple of nodes. Sizes stay tiny: the
    cut enumeration is complete, on purpose.
    """
    if count <= 0:
        raise CorpusError(f"no networks from {count}")
    rng = random.Random(seed)
    graphs: list = []
    seen: set = set()
    while len(graphs) < count:
        size = rng.randint(2, 8)
        graph = Graph()
        for node in range(size):
            graph.add_node(node)
        for step in range(size - 1):
            graph.add_edge(step, step + 1, rng.randint(0, 9))
        for _ in range(rng.randint(0, size)):
            start = rng.randrange(size - 1)
            end = rng.randrange(start + 1, size)
            graph.add_edge(start, end, rng.randint(0, 9))
        text = graph.to_text()
        if text in seen:
            continue
        seen.add(text)
        graphs.append(graph)
    return graphs


def load_graphs(path: str) -> list:
    """One network per line; blank lines and # comments skipped."""
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
            raise CorpusError(f"the corpus holds {stripped!r}, no network: {failure}") from failure
    if not graphs:
        raise CorpusError(f"{path} names no networks")
    return graphs


def write_graphs(graphs: list, path: str) -> None:
    """Write a corpus, one network per line, ended by a newline."""
    try:
        Path(path).write_text(
            "\n".join(graph.to_text() for graph in graphs) + "\n",
            encoding="utf-8",
        )
    except OSError as failure:
        raise CorpusError(f"cannot write {path}: {failure}") from failure


def report_lines(graphs: list) -> list:
    """Walk the corpus and answer line by line, flow value and cut value."""
    from .oracle import min_cut
    from .solve import max_flow

    lines: list = []
    for graph in graphs:
        source, sink = min(graph.nodes()), max(graph.nodes())
        walked = max_flow(graph, source, sink)
        least = min_cut(graph, source, sink)
        lines.append(
            f"{len(graph)} nodes {source}->{sink} flow {walked} cut {least} "
            f"equal={walked == least} {graph.to_text()[:36]!r}"
        )
    return lines
