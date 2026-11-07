"""The promises this grower makes, run against the real modules.

Every claim here is the reason a spanning tree can be trusted:
the grower's tree costs the enumeration oracle's minimum on
shipped and seeded corpora; the tree spans every node exactly once
with |V|-1 edges; ties pick the same tree run after run; and noise
answers loudly. Runnable in a fresh checkout:
`python -m the-package selftest`.
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
    is_connected,
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
    OracleError,
    min_cost,
    oracle_cost,
    spanning_trees,
    tree_total,
)
from .solve import (
    TreeError,
    audit,
    spanning_tree,
    tree_cost,
)

FIXTURE = "a node joins the tree once, through the cheapest crossing edge"
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
    for low, high, weight in LATTICE:
        graph.add_edge(low, high, weight)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and spoken weights")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an edge admits both ends", len(Graph().add_edge(2, 3, 1)), 2)
    report.equal("an edge is held both ways",
                 Graph().add_edge(2, 3, 7).neighbours(3), ((2, 7),))
    report.equal("an edge is answered once", Graph().add_edge(2, 3, 7).edges(),
                 (((2, 3), 7),))
    report.equal("labels come back sorted", Graph().add_edge(9, 1, 2).nodes(), (1, 9))
    report.refuses("a loop is refused", lambda: Graph().add_edge(3, 3, 1), GraphError)
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


def _enumeration(report: Report) -> None:
    report.section("the enumeration draws every tree, keeps the least")
    lattice = _lattice()
    trees = spanning_trees(lattice)
    report.ok("the enumeration draws at least one tree", len(trees) >= 1)
    report.equal("the enumeration's least is the grower's total", min_cost(lattice),
                 tree_cost(lattice, 1))
    report.equal("the oracle answers the same least", oracle_cost(lattice), min_cost(lattice))
    report.equal("a drawn set totals its weights",
                 tree_total(frozenset({((1, 2), 4)})), 4)
    chain = Graph()
    chain.add_edge(1, 2, 5)
    report.equal("a pair draws one tree", spanning_trees(chain), [frozenset({((1, 2), 5)})])
    lone = Graph()
    lone.add_node(4)
    report.equal("a lone node spans empty", min_cost(lone), 0)
    apart = Graph()
    apart.add_edge(1, 2, 1)
    apart.add_node(9)
    report.refuses("a graph in pieces draws no trees", lambda: spanning_trees(apart),
                   OracleError)
    report.refuses("a graph in pieces names no minimum", lambda: min_cost(apart), OracleError)


def _growth(report: Report) -> None:
    report.section("the grower answers the enumeration, total for total")
    lattice = _lattice()
    grown = spanning_tree(lattice, 1)
    report.equal("the lattice grows the enumeration's least", tree_cost(lattice, 1),
                 min_cost(lattice))
    report.equal("the audit stays silent", audit(lattice, 1, grown), [])
    report.equal("the tree holds one edge fewer than nodes", len(grown), len(lattice) - 1)
    report.equal("the grower's total is the same from any start",
                 tree_cost(lattice, 5), tree_cost(lattice, 3))
    ties = Graph()
    for low, high, weight in ((1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, 2)):
        ties.add_edge(low, high, weight)
    report.equal("equal weights pick the same tree twice",
                 spanning_tree(ties, 1), spanning_tree(ties, 1))
    report.equal("the tied tree is the enumeration's least", tree_cost(ties, 1),
                 min_cost(ties))
    lone = Graph()
    lone.add_node(4)
    report.equal("a lone node spans empty", spanning_tree(lone, 4), frozenset())
    report.refuses("a stranger starts nothing", lambda: spanning_tree(lattice, 99), KeyError)


def _pieces(report: Report) -> None:
    report.section("a graph in pieces is named, never spanned")
    apart = Graph()
    for low, high, weight in ((1, 2, 3), (7, 8, 1)):
        apart.add_edge(low, high, weight)
    report.equal("two pairs are two pieces", is_connected(apart), False)
    report.refuses("a piece cannot grow the whole", lambda: spanning_tree(apart, 1), TreeError)
    report.refuses("a piece totals no cost", lambda: tree_cost(apart, 7), TreeError)


def _trees(report: Report) -> None:
    report.section("every tree holds its own shape")
    for graph in synthetic(30, seed=7):
        start = min(graph.nodes())
        grown = spanning_tree(graph, start)
        if audit(graph, start, grown) or tree_cost(graph, start) != min_cost(graph):
            report.equal(f"{graph.to_text()[:24]!r} answered a loud tree", "break", "none")
            return
    report.ok("a seeded corpus answered silent trees, graph after graph", True)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the report out")
    corpus = synthetic(12, seed=5)
    report.equal("the generator is deterministic", [g.to_text() for g in corpus],
                 [g.to_text() for g in synthetic(12, seed=5)])
    report.ok("the graphs are distinct", len({g.to_text() for g in corpus}) == 12)
    report.ok("every generated graph is one piece", all(is_connected(g) for g in corpus))
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
    report.section("the tangle: a random weighted graph, answered twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(40):
            size = rng.randint(2, 7)
            graph = Graph()
            for node in range(size):
                graph.add_node(node)
            for node in range(1, size):
                graph.add_edge(node, rng.randrange(node), rng.randint(0, 9))
            for _ in range(rng.randint(0, size)):
                a = rng.randrange(size)
                b = rng.randrange(size)
                if a != b:
                    graph.add_edge(a, b, rng.randint(0, 9))
            start = min(graph.nodes())
            grown = spanning_tree(graph, start)
            if tree_cost(graph, start) != min_cost(graph):
                broke = True
                break
            if audit(graph, start, grown) or len(grown) != size - 1:
                broke = True
                break
        report.ok(f"forty tangles agreed with the enumeration (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the grower module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _enumeration(report)
    _growth(report)
    _pieces(report)
    _trees(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
