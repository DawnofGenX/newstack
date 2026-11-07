"""The promises this walker makes, run against the real modules.

Every claim here is the reason the distance map can be trusted:
the walker's map is the relaxation oracle's map on shipped and
seeded corpora; every shipped route costs what the map says;
unreachable nodes stay out of every map; and noise answers loudly.
Runnable in a fresh checkout: `python -m the-package selftest`.
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
from .graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)
from .oracle import (
    oracle_distances,
    relax_map,
)
from .solve import (
    RouteError,
    audit,
    distances,
    path,
)

FIXTURE = "a node is settled only when no edge can lower its cost"
LATTICE = (
    (1, 2, 4),
    (2, 3, 1),
    (1, 4, 2),
    (4, 3, 1),
    (3, 5, 3),
    (4, 5, 8),
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
    for source, target, weight in LATTICE:
        graph.add_edge(source, target, weight)
    graph.add_node(6)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and spoken weights")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an edge admits both ends", len(Graph().add_edge(2, 3, 1)), 2)
    report.equal("an edge carries its weight", Graph().add_edge(2, 3, 7).edges(),
                 ((2, 3, 7),))
    report.equal("labels come back sorted", Graph().add_edge(9, 1, 2).nodes(), (1, 9))
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a float weight is refused", lambda: Graph().add_edge(1, 2, 1.5),
                   GraphError)
    report.refuses("a negative weight is refused", lambda: Graph().add_edge(1, 2, -1),
                   GraphError)
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
    report.equal("a graph survives its text face", parse_graph(_lattice().to_text()).edges(),
                 _lattice().edges())
    report.refuses("a weightless edge is refused", lambda: parse_graph("1>2"), GraphError)
    report.refuses("noise is no graph", lambda: parse_graph("a > b"), GraphError)
    report.refuses("nothing is no graph", lambda: parse_graph("  "), GraphError)


def _fixed_point(report: Report) -> None:
    report.section("the fixed point relaxes, the oracle answers")
    lattice = _lattice()
    costs = relax_map(lattice, 1)
    report.equal("the source sits at zero", costs[1], 0)
    report.equal("the cheap lane beats the long one", costs[3], 3)
    report.equal("the oracle answers the same map", oracle_distances(lattice, 1), costs)
    report.equal("an island is no key", 6 in costs, False)
    report.refuses("a stranger sources nothing", lambda: relax_map(lattice, 99), KeyError)


def _walk(report: Report) -> None:
    report.section("the walker answers the fixed point, key for key")
    lattice = _lattice()
    walked = distances(lattice, 1)
    report.equal("the lattice walks as the fixed point answers", walked,
                 relax_map(lattice, 1))
    report.equal("the audit stays silent", audit(lattice, 1, walked), [])
    route, cost = path(lattice, 1, 5)
    report.equal("the route is the cheap lane", route, (1, 4, 3, 5))
    report.equal("the route costs the map's cost", cost, walked[5])
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, step + 1)
    report.equal("a chain walks the whole length", distances(chain, 0),
                 relax_map(chain, 0))
    report.equal("the chain's far end is the sum", distances(chain, 0)[9], 45)
    lone = Graph()
    lone.add_node(4)
    report.equal("a lone node maps to zero", distances(lone, 4), {4: 0})
    report.equal("the lone route is itself", path(lone, 4, 4), ((4,), 0))


def _islands(report: Report) -> None:
    report.section("unreachable stays honest: omitted, never invented")
    lattice = _lattice()
    report.equal("the island keeps no key", 6 in distances(lattice, 1), False)
    report.equal("the island's oracle key count", len(distances(lattice, 6)), 1)
    behind = Graph()
    for source, target, weight in ((1, 2, 3), (7, 8, 1)):
        behind.add_edge(source, target, weight)
    report.equal("a separated pair maps its own end", distances(behind, 7), {7: 0, 8: 1})
    report.refuses("a beyond-reach route is refused", lambda: path(lattice, 1, 6), RouteError)
    report.refuses("a stranger target is refused", lambda: path(lattice, 1, 99), KeyError)


def _maps(report: Report) -> None:
    report.section("every map holds its own shape")
    for graph in synthetic(30, seed=7):
        source = min(graph.nodes())
        costs = distances(graph, source)
        if audit(graph, source, costs) or costs != relax_map(graph, source):
            report.equal(f"{graph.to_text()[:24]!r} answered a loud map", "break", "none")
            return
    report.ok("a seeded corpus answered silent maps, graph after graph", True)


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
        path_name = f"{room}/graphs.txt"
        write_graphs(corpus, path_name)
        report.equal(
            "a written corpus reads back",
            [g.to_text() for g in load_graphs(path_name)],
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
    report.section("the tangle: a random weighted digraph, answered twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(60):
            graph = Graph()
            labels = rng.sample(range(0, MAX_LABEL, 7), rng.randint(2, 10))
            for node in labels:
                graph.add_node(node)
            for _ in range(rng.randint(1, len(labels) * len(labels) // 2)):
                graph.add_edge(rng.choice(labels), rng.choice(labels), rng.randint(0, 9))
            source = min(labels)
            if distances(graph, source) != relax_map(graph, source):
                broke = True
                break
            for target in graph.nodes():
                route = path(graph, source, target) if target in distances(graph, source) \
                    else None
                if route is not None and route[1] != relax_map(graph, source)[target]:
                    broke = True
                    break
        report.ok(f"sixty tangles agreed with the fixed point (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the walker module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _fixed_point(report)
    _walk(report)
    _islands(report)
    _maps(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
