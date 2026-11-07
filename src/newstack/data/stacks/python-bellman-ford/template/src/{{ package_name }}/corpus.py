"""Weighted graphs in, reports out: corpora, generators, snapshots.

One graph per line, tokens spaced apart; blank lines and # comments
are skipped and every other line must pass the parser's gate. The
generator is deterministic from its seed, so a frozen corpus replays
its graphs exactly, in order, forever - and every graph it generates
is acyclic, so the walk always settles.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .graph import UNREACHED, Graph, GraphError, parse_graph

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


def _quiet_graph(rng: random.Random, size: int) -> Graph:
    """An acyclic weighted graph: labels shuffled, edges only downstream.

    Edges run one way down a shuffled order, so no cycle exists and
    no cycle can drag a walk down - but the labels arrive shuffled,
    so a sorted sweep really needs its |V|-1 rounds.
    """
    order = list(range(size))
    rng.shuffle(order)
    graph = Graph()
    for label in order:
        graph.add_node(label)
    for head in range(size):
        for tail in range(head + 1, size):
            if rng.random() < rng.choice((0.2, 0.35, 0.5)):
                graph.add_edge(
                    order[head], order[tail], rng.randint(-9, 9)
                )
    if not graph.edges():
        graph.add_edge(order[0], order[-1], rng.randint(-9, 9))
    return graph


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list:
    """A deterministic list of small weighted digraphs, acyclic by build."""
    if count <= 0:
        raise CorpusError(f"no graphs from {count}")
    rng = random.Random(seed)
    graphs: list = []
    seen: set = set()
    while len(graphs) < count:
        graph = _quiet_graph(rng, rng.randint(2, 12))
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
    """Walk the corpus and answer line by line, walked vs walked-past."""
    from .walk import distances, settled

    lines: list = []
    for graph in graphs:
        answer = distances(graph, graph.nodes()[0])
        reached = sum(1 for cost in answer.values() if cost is not UNREACHED)
        quiet = not settled(graph, graph.nodes()[0])
        lines.append(
            f"{len(graph)} nodes -> walked {reached} settled {quiet} "
            f"{graph.to_text()[:36]!r}"
        )
    return lines
