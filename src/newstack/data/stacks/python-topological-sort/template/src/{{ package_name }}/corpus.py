"""Graphs in, reports out: corpora, generators, snapshots, tangles.

One graph per line, tokens spaced apart; blank lines and # comments
are skipped and every other line must pass the door. The generator
is deterministic from its seed, so a frozen corpus replays its
graphs - edges and all - exactly, in order, forever. The shipped
tangles are the cyclic fixtures: cycle() names them, order() refuses
around them.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .graph import Graph, GraphError, parse_graph

DEFAULT_SEED = 20261107

TANGLES = (
    "1 2 3 1>2 2>3 3>1",
    "4 5 6 7 4>5 5>6 6>4 6>7",
    "10 20 30 40 50 10>20 20>30 30>10 30>40 40>50 50>40",
)


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
    """A deterministic list of small DAGs, sparse and partly islanded.

    Edges only ever run from an earlier label on the shuffle to a
    later one, so every generated graph orders; some generators shut
    a node's doors on purpose: a corpus with no island proves
    nothing about listing every node once.
    """
    if count <= 0:
        raise CorpusError(f"no graphs from {count}")
    rng = random.Random(seed)
    graphs: list = []
    seen: set = set()
    while len(graphs) < count:
        size = rng.randint(2, 12)
        parade = rng.sample(range(0, 98, 7), size)
        graph = Graph()
        for node in parade:
            graph.add_node(node)
        for rank, source in enumerate(parade):
            for target in parade[rank + 1:]:
                if rng.random() < rng.choice((0.15, 0.3, 0.45)):
                    graph.add_edge(source, target)
        text = graph.to_text()
        if text in seen:
            continue
        seen.add(text)
        graphs.append(graph)
    return graphs


def tangles() -> list:
    """The shipped cyclic fixtures: graphs the order refuses."""
    return [parse_graph(line) for line in TANGLES]


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
    """Walk the corpus line by line: placed count, block count, the graph."""
    from .order import block

    lines: list = []
    for graph in graphs:
        held = block(graph)
        lines.append(
            f"{len(graph)} nodes, {len(graph) - len(held)} placed, "
            f"{len(held)} held by a block {graph.to_text()[:36]!r}"
        )
    return lines
