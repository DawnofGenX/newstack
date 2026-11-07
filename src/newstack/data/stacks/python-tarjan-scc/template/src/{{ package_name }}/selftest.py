"""The promises this walker makes, run against the real modules.

Every claim here is the reason the partition can be trusted: the
walker's answer is the oracle's partition on shipped and seeded
corpora; every node lands in exactly one component; the condensed
graph clears the cycle checker; and noise answers loudly. Runnable
in a fresh checkout: `python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
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
    audit,
    condense,
    partition,
    strong_components,
)

FIXTURE = "two nodes share a component only when each reaches the other"
DIAMOND = (
    (1, 2),
    (2, 3),
    (3, 1),
    (3, 4),
    (4, 5),
    (5, 4),
    (4, 6),
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


def _diamond() -> Graph:
    graph = Graph()
    for source, target in DIAMOND:
        graph.add_edge(source, target)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and refuses noise")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an edge admits both ends", len(Graph().add_edge(2, 3)), 2)
    report.equal("labels come back sorted", Graph().add_edge(9, 1).nodes(), (1, 9))
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a past-ceiling label is refused", lambda: Graph().add_node(MAX_LABEL + 1),
                   GraphError)
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    report.refuses(
        "one node past the ceiling is refused",
        lambda: crowded.add_node(MAX_NODES),
        GraphError,
    )
    report.equal("a graph survives its text face", parse_graph(_diamond().to_text()).edges(),
                 _diamond().edges())
    report.refuses("noise is no graph", lambda: parse_graph("a > b"), GraphError)
    report.refuses("nothing is no graph", lambda: parse_graph("  "), GraphError)


def _closure(report: Report) -> None:
    report.section("the closure reaches, the oracle answers")
    diamond = _diamond()
    reached = reach(diamond)
    report.ok("a node reaches itself", 1 in reached[1])
    report.ok("the ring reaches its head", 1 in reached[3])
    report.equal("the tail reaches only itself", reached[6], frozenset({6}))
    report.equal(
        "the oracle splits the diamond",
        oracle_partition(diamond),
        (frozenset({1, 2, 3}), frozenset({4, 5}), frozenset({6})),
    )


def _walk(report: Report) -> None:
    report.section("the walker answers the oracle, component for component")
    diamond = _diamond()
    report.equal("the diamond walks as the closure answers", partition(diamond),
                 oracle_partition(diamond))
    report.equal("the published spelling agrees", strong_components(diamond),
                 list(partition(diamond)))
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1)
    report.equal("a chain walks apart", partition(chain), oracle_partition(chain))
    ring = Graph()
    for step in range(8):
        ring.add_edge(step, (step + 1) % 8)
    report.equal("a ring walks whole", len(partition(ring)), 1)
    report.equal("a ring agrees with the closure", partition(ring), oracle_partition(ring))
    empty = Graph()
    empty.add_node(4)
    report.equal("a lone node is its own component", partition(empty), (frozenset({4}),))


def _seats(report: Report) -> None:
    report.section("every node lands in exactly one component")
    diamond = _diamond()
    groups = partition(diamond)
    report.equal("the diamond audits silent", audit(diamond, groups), [])
    seats = [member for group in groups for member in group]
    report.equal("the seats are the nodes", sorted(seats), sorted(diamond.nodes()))
    for graph in synthetic(30, seed=7):
        if audit(graph, partition(graph)):
            report.equal(f"{graph.to_text()[:24]!r} answered loud seats", "break", "none")
            return
    report.ok("a seeded corpus audited silent, graph after graph", True)


def _fold(report: Report) -> None:
    report.section("the folded graph is a graph the checker clears")
    diamond = _diamond()
    dag = condense(diamond)
    report.equal("the fold keeps the heads", sorted(dag.nodes()), [1, 4, 6])
    report.equal("the fold keeps the crossings", sorted(dag.edges()), [(1, 4), (4, 6)])
    report.equal("the cycle checker clears the fold", has_cycle(dag), None)
    for graph in synthetic(30, seed=91):
        if has_cycle(condense(graph)):
            report.equal(f"{graph.to_text()[:24]!r} folded cyclic", "break", "none")
            return
    report.ok("a seeded corpus folded acyclic, graph after graph", True)
    ring = Graph()
    for step in range(6):
        ring.add_edge(step, (step + 1) % 6)
    report.equal("a ring folds to one bare head", sorted(condense(ring).nodes()), [0])
    report.equal("the fold drops every inside edge", condense(ring).edges(), ())


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
        path = f"{room}/graphs.txt"
        write_graphs(corpus, path)
        report.equal(
            "a written corpus reads back",
            [g.to_text() for g in load_graphs(path)],
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


def _tangles(report: Report) -> None:
    report.section("the tangle: a random digraph, answered twice")
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
            if partition(graph) != oracle_partition(graph):
                broke = True
                break
        report.ok(f"sixty tangles agreed with the closure (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import scc as scc_module

    report.ok(
        "the marker the detector looks for is in the walker module",
        FIXTURE in " ".join((scc_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _closure(report)
    _walk(report)
    _seats(report)
    _fold(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
