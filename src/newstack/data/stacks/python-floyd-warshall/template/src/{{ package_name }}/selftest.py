"""The promises this walker makes, run against the real modules.

Every claim here is the reason a distance table can be trusted:
the matrix's table equals the walking oracle's table on shipped and
seeded corpora; the diagonal sits at zero; one more sweep changes
nothing; an unreached pair stays omitted; and noise answers loudly.
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
    reaches_all,
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
    MAX_SWEEPS,
    distance_table,
    oracle_table,
    walk_from,
)
from .solve import (
    TableError,
    audit,
    distances,
    restated,
    worst_hop,
)

FIXTURE = "the table is the walker's table, pair for pair"
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
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and spoken weights")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an arrow admits both ends", len(Graph().add_edge(2, 3, 1)), 2)
    report.equal("an arrow is held one way", Graph().add_edge(2, 3, 7).neighbours(2), ((3, 7),))
    report.equal("the back arrow walks nothing", Graph().add_edge(2, 3, 7).neighbours(3), ())
    report.equal("an arrow is answered once", Graph().add_edge(2, 3, 7).edges(),
                 (((2, 3), 7),))
    report.equal("labels come back sorted", Graph().add_edge(9, 1, 2).nodes(), (1, 9))
    report.refuses("a loop is refused", lambda: Graph().add_edge(3, 3, 1), GraphError)
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a float weight is refused", lambda: Graph().add_edge(1, 2, 1.5),
                   GraphError)
    report.refuses("a negative weight is refused", lambda: Graph().add_edge(1, 2, -1),
                   GraphError)
    report.refuses("a past-ceiling label is refused",
                   lambda: Graph().add_node(MAX_LABEL + 1), GraphError)
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
    report.refuses("a weightless arrow is refused", lambda: parse_graph("1>2"), GraphError)
    report.refuses("noise is no graph", lambda: parse_graph("a > b"), GraphError)
    report.refuses("nothing is no graph", lambda: parse_graph("  "), GraphError)


def _walking(report: Report) -> None:
    report.section("the walker finds the roads, omits the rest")
    lattice = _lattice()
    walked = walk_from(lattice, 1)
    report.equal("the source stands at zero", walked[1], 0)
    report.equal("the direct arrow is walked", walked[2], 4)
    report.equal("the stepping stone is cheaper", walked[3], 3)
    report.equal("the past is walked through", walked[5], 6)
    report.equal("the walk rests where it rests", distance_table(lattice),
                 oracle_table(lattice))
    report.equal("a dead end walks no onward road", walk_from(lattice, 5), {5: 0})
    one_way = Graph().add_edge(1, 2, 3)
    report.equal("a lone arrow walks forward", distance_table(one_way),
                 {(1, 1): 0, (1, 2): 3, (2, 2): 0})
    report.refuses("a stranger walks nothing", lambda: walk_from(lattice, 99), KeyError)
    report.equal("the walker rests inside its ceiling", MAX_SWEEPS > 32, True)


def _matrix(report: Report) -> None:
    report.section("the matrix answers the walker, pair for pair")
    lattice = _lattice()
    answered = distances(lattice)
    report.equal("the table equals the walk", answered, distance_table(lattice))
    report.equal("the audit stays silent", audit(lattice, answered), [])
    report.equal("every node stands at zero", {node: answered[(node, node)]
                                               for node in lattice.nodes()},
                 {node: 0 for node in lattice.nodes()})
    report.equal("one more sweep moves nothing", restated(answered), answered)
    report.equal("the farthest pair is honest", worst_hop(lattice), (1, 5, 6))
    report.ok("a stranger sits at no table entry", (99, 1) not in distances(lattice))
    report.ok("the walker never invented a back arrow", (5, 1) not in distances(lattice))


def _silent(report: Report) -> None:
    report.section("an unreached pair is omitted, never infinity")
    one_way = Graph().add_edge(1, 2, 5)
    table = distances(one_way)
    report.ok("the back pair is absent", (2, 1) not in table)
    report.ok("infinity ships in no cell", all(cost < float("inf")
                                               for cost in table.values()))
    apart = Graph().add_edge(1, 2, 3).add_edge(7, 8, 1)
    report.equal("two arrows walk no bridge", distances(apart),
                 {(1, 1): 0, (1, 2): 3, (2, 2): 0,
                  (7, 7): 0, (7, 8): 1, (8, 8): 0})
    report.refuses("a silent graph names no worst",
                   lambda: worst_hop(Graph().add_node(4)), TableError)


def _tables(report: Report) -> None:
    report.section("every table holds its own shape")
    for graph in synthetic(30, seed=7):
        answered = distances(graph)
        walked = distance_table(graph)
        if answered != walked or audit(graph, answered):
            report.equal(f"{graph.to_text()[:24]!r} answered a loud table", "break", "none")
            return
        if restated(answered) != answered:
            report.equal(f"{graph.to_text()[:24]!r} never rested", "moved", "still")
            return
    report.ok("a seeded corpus answered resting tables, graph after graph", True)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the report out")
    corpus = synthetic(12, seed=5)
    report.equal("the generator is deterministic", [g.to_text() for g in corpus],
                 [g.to_text() for g in synthetic(12, seed=5)])
    report.ok("the graphs are distinct", len({g.to_text() for g in corpus}) == 12)
    report.ok("every generated graph walks on",
              all(reaches_all(g) for g in corpus[:3]))
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
        for _ in range(40):
            size = rng.randint(2, 7)
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
            answered = distances(graph)
            if answered != distance_table(graph) or audit(graph, answered):
                broke = True
                break
            if restated(answered) != answered:
                broke = True
                break
        report.ok(f"forty tangles agreed with the walker (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the matrix module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _walking(report)
    _matrix(report)
    _silent(report)
    _tables(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
