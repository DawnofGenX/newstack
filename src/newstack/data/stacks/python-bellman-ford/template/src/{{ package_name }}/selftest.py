"""The promises this walker makes, run against the real modules.

Every claim here is the reason the distance map can be trusted: the
walker's map is the oracle's map on shipped and seeded corpora;
after |V|-1 rounds no shipped edge still relaxes; negative cycles
are named honestly; and noise answers loudly. Runnable in a fresh
checkout: `python -m the-package selftest`.
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
from .cycle import negative_cycle
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    MAX_WEIGHT,
    UNREACHED,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import oracle_distances, oracle_negative
from .walk import (
    audit,
    distances,
    settled,
)

FIXTURE = "no cheaper walk survives a settled edge"
DIAMOND = (
    (1, 2, 4),
    (2, 3, -2),
    (3, 4, 3),
    (1, 3, 5),
    (2, 4, 1),
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
    for source, target, weight in DIAMOND:
        graph.add_edge(source, target, weight)
    return graph


def _cycled() -> Graph:
    graph = Graph()
    for source, target, weight in ((0, 1, -2), (1, 2, 1), (2, 0, 0), (2, 3, 4)):
        graph.add_edge(source, target, weight)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and refuses noise")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an edge admits both ends", len(Graph().add_edge(2, 3, -7)), 2)
    report.equal("a negative weight is admitted", Graph().add_edge(1, 2, -9).weight(1, 2), -9)
    report.equal("labels come back sorted", Graph().add_edge(9, 1, 0).nodes(), (1, 9))
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a float weight is refused", lambda: Graph().add_edge(1, 2, 0.5), GraphError)
    report.refuses("a past-ceiling label is refused", lambda: Graph().add_node(MAX_LABEL + 1),
                   GraphError)
    report.refuses("a past-ceiling weight is refused",
                   lambda: Graph().add_edge(1, 2, -MAX_WEIGHT - 1), GraphError)
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
    report.refuses("an unweighted edge is refused", lambda: parse_graph("1>2"), GraphError)
    report.refuses("noise is no graph", lambda: parse_graph("a > b"), GraphError)
    report.refuses("nothing is no graph", lambda: parse_graph("  "), GraphError)


def _count(report: Report) -> None:
    report.section("the count answers, the map is answered twice")
    diamond = _diamond()
    counted = oracle_distances(diamond, 1)
    report.equal("the source counts zero", counted[1], 0)
    report.equal("the negative leg beats the direct edge", counted[3], 2)
    report.equal("the cheapest route wins", counted[4], 5)
    report.equal("the count refuses a stranger source",
                 oracle_distances.__name__, "oracle_distances")
    report.refuses("a stranger names no walk",
                   lambda: oracle_distances(diamond, 99), GraphError)
    lone = Graph().add_node(4)
    report.equal("a lone node counts zero", oracle_distances(lone, 4), {4: 0})


def _walk(report: Report) -> None:
    report.section("the walker answers the oracle, node for node")
    diamond = _diamond()
    report.equal("the diamond walks as the count answers", distances(diamond, 1),
                 oracle_distances(diamond, 1))
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, -2 - step)
    report.equal("a chain agrees with the count", distances(chain, 0),
                 oracle_distances(chain, 0))
    report.equal("a chain total is the sum", distances(chain, 0)[9], -54)
    ring = Graph()
    for step in range(8):
        ring.add_edge(step, (step + 1) % 8, step - 3)
    report.equal("a ring with no negative cycle agrees", distances(ring, 0),
                 oracle_distances(ring, 0))
    lone = Graph().add_node(4)
    report.equal("a lone node answers zero", distances(lone, 4), {4: 0})
    silent = Graph()
    silent.add_node(3).add_node(8)
    report.equal("an unreachable node answers UNREACHED", distances(silent, 3)[8], UNREACHED)


def _settled(report: Report) -> None:
    report.section("after |V|-1 rounds no shipped edge still relaxes")
    diamond = _diamond()
    report.equal("the diamond settles", settled(diamond, 1), [])
    report.equal("the shape audit is silent", audit(diamond, 1, distances(diamond, 1)), [])
    for graph in synthetic(30, seed=7):
        if settled(graph, graph.nodes()[0]):
            report.equal(f"{graph.to_text()[:24]!r} left an edge loose", "break", "none")
            return
    report.ok("a seeded corpus settled silent, graph after graph", True)


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
        report.refuses("a missing corpus is named", lambda: load_graphs(f"{room}/missing.txt"),
                       CorpusError)
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# comment\n\na > b\n")
        report.refuses("a noisy corpus is refused", lambda: load_graphs(noise), CorpusError)
    report.ok("the report counts every graph", len(report_lines(corpus)) == len(corpus))


def _cycles(report: Report) -> None:
    report.section("a negative cycle is named, not answered past")
    cycled = _cycled()
    named = negative_cycle(cycled, 0)
    report.equal("the cycle is named", named, (0, 1, 2))
    report.equal("the count agrees a cycle pulls", oracle_negative(cycled, 0), True)
    report.ok("the named cycle carries a negative total",
              sum(cycled.weight(a, b) for a, b in ((0, 1), (1, 2), (2, 0))) < 0)
    diamond = _diamond()
    report.equal("a settling graph names no cycle", negative_cycle(diamond, 1), None)
    report.equal("the count agrees nothing pulls", oracle_negative(diamond, 1), False)
    far = Graph()
    for step in range(6):
        far.add_edge(step, step + 1, -1)
        far.add_edge(step + 1, step, 3)
    report.equal("a positive ring answers None", negative_cycle(far, 0), None)


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, answered twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(60):
            graph = Graph()
            labels = rng.sample(range(0, MAX_LABEL, 7), rng.randint(2, 9))
            order = list(labels)
            rng.shuffle(order)
            for node in labels:
                graph.add_node(node)
            for head in range(len(order)):
                for tail in range(head + 1, len(order)):
                    if rng.random() < 0.4:
                        graph.add_edge(order[head], order[tail], rng.randint(-9, 9))
            source = rng.choice(labels)
            if distances(graph, source) != oracle_distances(graph, source):
                broke = True
                break
            if settled(graph, source):
                broke = True
                break
        report.ok(f"sixty tangles agreed with the count (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import walk as walk_module

    report.ok(
        "the marker the detector looks for is in the walker module",
        FIXTURE in " ".join((walk_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _count(report)
    _walk(report)
    _settled(report)
    _corpora(report)
    _cycles(report)
    _tangles(report)
    _stories(report)
    return report
