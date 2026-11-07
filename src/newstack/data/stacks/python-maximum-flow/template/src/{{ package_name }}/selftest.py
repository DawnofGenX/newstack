"""The promises this walker makes, run against the real modules.

Every claim here is the reason carried flow can be trusted: the
walker's value equals the brute-force cut enumeration's least on
shipped and seeded corpora; the shipped map conserves at every
interior node and never walks past a capacity; the same network
walks to the same map run after run; and noise answers loudly.
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
    has_route,
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
    cut_capacity,
    cuts,
    least_cut,
    min_cut,
    oracle_value,
)
from .solve import (
    FlowError,
    audit,
    flow_map,
    max_flow,
)

FIXTURE = "flow walks the residual, never past a bottleneck"
DIAMOND = (
    (0, 1, 3),
    (1, 3, 2),
    (0, 2, 2),
    (2, 3, 3),
    (0, 3, 1),
    (1, 2, 1),
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
    for start, end, room in DIAMOND:
        graph.add_edge(start, end, room)
    return graph


def _door(report: Report) -> None:
    report.section("the door admits small integers and spoken capacities")
    graph = Graph()
    report.equal("a node is admitted", (graph.add_node(7).nodes()), (7,))
    report.equal("an arc admits both ends", len(Graph().add_edge(2, 3, 1)), 2)
    report.equal("an arc is held one way only",
                 Graph().add_edge(2, 3, 7).out_arcs(2), ((3, 7),))
    report.equal("the reverse of an arc is silent", Graph().add_edge(2, 3, 7).out_arcs(3), ())
    report.equal("arcs come back lowest source first",
                 Graph().add_edge(9, 1, 2).edges(), (((9, 1), 2),))
    report.equal("a repeated arc merges its capacity",
                 Graph().add_edge(2, 3, 4).add_edge(2, 3, 5).out_arcs(2), ((3, 9),))
    report.refuses("a loop is refused", lambda: Graph().add_edge(3, 3, 1), GraphError)
    report.refuses("the opposite arc of a channel is refused",
                   lambda: Graph().add_edge(2, 3, 1).add_edge(3, 2, 1), GraphError)
    report.refuses("a float label is refused", lambda: Graph().add_node(1.5), GraphError)
    report.refuses("a float capacity is refused", lambda: Graph().add_edge(1, 2, 1.5),
                   GraphError)
    report.refuses("a negative capacity is refused", lambda: Graph().add_edge(1, 2, -1),
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
    report.equal("a network survives its text face",
                 parse_graph(_diamond().to_text()).edges(), _diamond().edges())
    report.refuses("a capacityless arc is refused", lambda: parse_graph("1>2"), GraphError)
    report.refuses("noise is no network", lambda: parse_graph("a > b"), GraphError)
    report.refuses("nothing is no network", lambda: parse_graph("  "), GraphError)


def _enumeration(report: Report) -> None:
    report.section("the enumeration draws every cut, keeps the least")
    diamond = _diamond()
    drawn = cuts(diamond, 0, 3)
    report.equal("the enumeration draws a cut per shore", len(drawn), 4)
    report.equal("the enumeration's least is the walker's value", min_cut(diamond, 0, 3),
                 max_flow(diamond, 0, 3))
    report.equal("the oracle answers the same least", oracle_value(diamond, 0, 3),
                 min_cut(diamond, 0, 3))
    report.equal("the least cut names its shore", least_cut(diamond, 0, 3), (6, (0,)))
    report.equal("a named shore pays its crossing", cut_capacity(diamond, {0, 1}), 6)
    chain = Graph()
    chain.add_edge(1, 2, 5)
    report.equal("a pair draws one real cut", min_cut(chain, 1, 2), 5)
    apart = Graph()
    apart.add_edge(1, 2, 4)
    apart.add_node(8)
    report.equal("a network with no route cuts to zero", min_cut(apart, 1, 8), 0)
    report.refuses("ends that match cut nothing", lambda: min_cut(diamond, 0, 0), OracleError)


def _walk(report: Report) -> None:
    report.section("the walker answers the enumeration, value for value")
    diamond = _diamond()
    shipped = flow_map(diamond, 0, 3)
    report.equal("the diamond carries the enumeration's least", max_flow(diamond, 0, 3),
                 min_cut(diamond, 0, 3))
    report.equal("the audit stays silent", audit(diamond, 0, 3, shipped), [])
    report.equal("the map ships what the source let go",
                 sum(amount for (start, _end), amount in shipped.items() if start == 0),
                 max_flow(diamond, 0, 3))
    report.equal("the walker is the same answer twice", flow_map(diamond, 0, 3),
                 flow_map(diamond, 0, 3))
    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    report.equal("a chain carries its least door", max_flow(chain, 0, 8), 1)
    stopped = Graph()
    stopped.add_edge(1, 2, 0)
    report.equal("a closed door carries nothing", max_flow(stopped, 1, 2), 0)
    apart = Graph()
    apart.add_edge(1, 2, 4)
    apart.add_node(8)
    report.equal("no route carries zero, not a refusal", max_flow(apart, 1, 8), 0)
    report.refuses("a stranger is no source", lambda: max_flow(diamond, 99, 3), KeyError)
    report.refuses("ends that match walk nothing", lambda: max_flow(diamond, 0, 0), FlowError)


def _corpora(report: Report) -> None:
    report.section("the corpus in, the report out")
    corpus = synthetic(12, seed=5)
    report.equal("the generator is deterministic", [g.to_text() for g in corpus],
                 [g.to_text() for g in synthetic(12, seed=5)])
    report.ok("the networks are distinct", len({g.to_text() for g in corpus}) == 12)
    report.ok("every generated network answers the enumeration",
              all(max_flow(g, min(g.nodes()), max(g.nodes()))
                  == min_cut(g, min(g.nodes()), max(g.nodes())) for g in corpus))
    report.refuses("no networks from zero", lambda: synthetic(0), CorpusError)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its networks", [g.to_text() for g in thawed.graphs()],
                 [g.to_text() for g in corpus])
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        CorpusError,
    )
    with TemporaryDirectory() as room:
        path_name = f"{room}/networks.txt"
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
    report.ok("the report counts every network", len(report_lines(corpus)) == len(corpus))
    report.ok("a route walks when one is owed", has_route(_diamond(), 0, 3))
    report.ok("no route is honest about its absence",
              not has_route(_diamond(), 3, 0))


def _tangles(report: Report) -> None:
    report.section("the tangle: a random network, walked twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _ in range(40):
            size = rng.randint(2, 7)
            graph = Graph()
            for node in range(size):
                graph.add_node(node)
            for start in range(size - 1):
                if rng.random() < 0.7:
                    graph.add_edge(start, start + 1, rng.randint(0, 9))
            for _ in range(rng.randint(0, size)):
                start = rng.randrange(size - 1)
                end = rng.randrange(start + 1, size)
                graph.add_edge(start, end, rng.randint(0, 9))
            source, sink = 0, size - 1
            shipped = flow_map(graph, source, sink)
            if max_flow(graph, source, sink) != min_cut(graph, source, sink):
                broke = True
                break
            if audit(graph, source, sink, shipped):
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
        "the marker the detector looks for is in the walker module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _enumeration(report)
    _walk(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
