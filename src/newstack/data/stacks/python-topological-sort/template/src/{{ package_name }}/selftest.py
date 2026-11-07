"""The promises this orderer makes, run against the real modules.

Every claim here is the reason a listing can be called an order: the
listing validates against every shipped edge, every node sits once,
the sequence is a fixed point, the picker answers the same sequence,
and a tangle names its block honestly. Runnable in a fresh checkout:
`python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
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

FIXTURE = "a node is released only when its last predecessor has gone"
LATTICE = (
    (1, 2),
    (1, 4),
    (2, 3),
    (4, 3),
    (3, 5),
    (4, 5),
)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})"
            if found == expected
            else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, call: object, error: type) -> None:
        try:
            call()  # type: ignore[operator]
        except error as seen:
            self.ok(f"{claim} ({seen})", True)
        except Exception as seen:
            self.ok(f"{claim}: raised {type(seen).__name__}, not {error.__name__}", False)
        else:
            self.ok(f"{claim}: nothing raised", False)

    def render(self) -> str:
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self.lines, "", tail))


def _lattice() -> Graph:
    graph = Graph()
    for source, target in LATTICE:
        graph.add_edge(source, target)
    graph.add_node(6)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and spoken pairs")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("a pair admits both ends", len(Graph().add_edge(2, 3)), 2)
    report.equal("a pair is directed", Graph().add_edge(2, 3).edges(), ((2, 3),))
    report.equal("labels come back sorted", Graph().add_edge(9, 1).nodes(), (1, 9))
    report.equal("a reverse pair is its own pair", Graph().add_edge(9, 1).edges(), ((9, 1),))
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a past-ceiling label is refused", lambda: Graph().add_node(MAX_LABEL + 1),
                   GraphError)
    report.refuses("a word is no pair", lambda: parse_graph("a>b"), GraphError)
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    report.refuses(
        "one node past the ceiling is refused",
        lambda: crowded.add_node(MAX_NODES),
        GraphError,
    )
    report.equal("a graph survives its text face", parse_graph(_lattice().to_text()).edges(),
                 _lattice().edges())
    report.refuses("a half pair is refused", lambda: parse_graph("1>2>3"), GraphError)
    report.refuses("noise is no graph", lambda: parse_graph("  "), GraphError)


def _ladder(report: Report) -> None:
    report.section("the ladder: predecessors before their targets")
    lattice = _lattice()
    listed = order(lattice)
    report.equal("the ladder lists its least first", listed[0], 1)
    report.equal("the ladder lists every node once", sorted(listed), sorted(lattice.nodes()))
    report.equal("the ladder answers the picker", listed, naive_order(lattice))
    report.equal("the ladder validates silent", validate(lattice, listed), [])
    report.equal("the ladder is a fixed point", order(lattice), listed)
    report.equal("a block stays nameless here", block(lattice), ())
    report.equal("no cycle tangles the ladder", cycle(lattice), None)
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1)
    report.equal("a chain lists its whole length", order(chain), tuple(range(10)))
    report.equal("the chain answers the picker", order(chain), naive_order(chain))
    lone = Graph()
    lone.add_node(4)
    report.equal("a lone node lists itself", order(lone), (4,))


def _islands(report: Report) -> None:
    report.section("every node is listed: islands included, none invented")
    lattice = _lattice()
    report.equal("the island is listed last", order(lattice)[-1], 6)
    report.equal("the island count is the node count", len(order(lattice)), len(lattice))
    behind = Graph()
    for source, target in ((1, 2), (7, 8)):
        behind.add_edge(source, target)
    report.equal("a separated pair lists its own end", order(behind), (1, 2, 7, 8))
    report.ok("a short listing is named broken", bool(validate(lattice, (1, 2))))
    report.ok("an invented seat is named broken", bool(validate(lattice, (1, 2, 3, 4, 5, 6, 7))))


def _maps(report: Report) -> None:
    report.section("every listing holds its own shape")
    for graph in synthetic(30, seed=7):
        listed = order(graph)
        if validate(graph, listed) or listed != naive_order(graph):
            report.equal(f"{graph.to_text()[:24]!r} answered a loud listing", "break", "none")
            return
    report.ok("a seeded corpus answered silent listings, graph after graph", True)


def _tangles(report: Report) -> None:
    report.section("a tangle names its block, the order refuses")
    for graph in tangles():
        named = cycle(graph)
        report.ok(f"the block is named on {graph.to_text()[:18]!r}", named is not None)
        report.refuses(f"the order refuses {graph.to_text()[:18]!r}", lambda g=graph: order(g),
                       OrderError)
        report.ok(f"the block is not empty on {graph.to_text()[:18]!r}", bool(block(graph)))
    report.equal("the shipped tangles are three", len(TANGLES), 3)
    ring = Graph()
    for source, target in ((4, 5), (5, 6), (6, 4)):
        ring.add_edge(source, target)
    report.equal("a ring names its ring", cycle(ring), (4, 5, 6))
    report.equal("a ring blocks its whole ring", block(ring), (4, 5, 6))
    half = Graph()
    for source, target in ((1, 2), (2, 3), (3, 2), (3, 4)):
        half.add_edge(source, target)
    report.equal("the block holds the tail too", block(half), (2, 3, 4))
    report.refuses("the order refuses a tail into a ring", lambda: order(half), OrderError)
    report.equal("a picker stalls on a ring", cycle(ring) is not None, True)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the report out")
    corpus = synthetic(12, seed=5)
    report.equal("the generator is deterministic", [g.to_text() for g in corpus],
                 [g.to_text() for g in synthetic(12, seed=5)])
    report.ok("the graphs are distinct", len({g.to_text() for g in corpus}) == 12)
    report.refuses("no graphs from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its graphs", [g.to_text() for g in thawed.graphs()],
                 [g.to_text() for g in corpus])
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        CorpusError,
    )
    with TemporaryDirectory() as room:
        name = f"{room}/graphs.txt"
        write_graphs(corpus, name)
        report.equal(
            "a written corpus reads back",
            [g.to_text() for g in load_graphs(name)],
            [g.to_text() for g in corpus],
        )
        report.refuses(
            "a missing corpus is named", lambda: load_graphs(f"{room}/missing.txt"),
            CorpusError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# comment\n\na > b\n")
        report.refuses("a noisy corpus is refused", lambda: load_graphs(noise), CorpusError)
    report.ok("the report counts every graph", len(report_lines(corpus)) == len(corpus))


def _tangles_random(report: Report) -> None:
    report.section("the tangle: a random graph, ordered or named twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(60):
            graph = Graph()
            labels = rng.sample(range(0, MAX_LABEL, 7), rng.randint(2, 10))
            for node in labels:
                graph.add_node(node)
            for _ in range(rng.randint(1, len(labels) * len(labels) // 2)):
                graph.add_edge(rng.choice(labels), rng.choice(labels))
            named = cycle(graph)
            held = block(graph)
            if named is None:
                if held or order(graph) != naive_order(graph) or validate(graph, order(graph)):
                    broke = True
                    break
            elif not held or cycle(graph) != named:
                broke = True
                break
        report.ok(f"sixty tangles answered honest either way (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    import importlib

    order_module = importlib.import_module(".order", __package__)
    report.ok(
        "the marker the detector looks for is in the order module",
        FIXTURE in " ".join((order_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _ladder(report)
    _islands(report)
    _maps(report)
    _tangles(report)
    _corpora(report)
    _tangles_random(report)
    _stories(report)
    return report
