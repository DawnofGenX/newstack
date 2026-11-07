"""Six stories about routes, every number computed live.

A story states a promise the walker owes the fixed point and
answers it against the real modules - no hand-written expectations,
no stored figures. If any story stops holding, the tool is wrong
and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .graph import Graph
from .oracle import relax_map
from .solve import audit, distances, path


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    graph.add_node(6)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    lattice = _lattice()
    walked = distances(lattice, 1)
    answer = relax_map(lattice, 1)
    first = Story(
        "the walker answers the fixed point, key for key",
        f"walked={len(walked)} oracle={len(answer)} equal={walked == answer}",
        walked == answer,
    )

    route, cost = path(lattice, 1, 5)
    third = Story(
        "every shipped route costs what the map says",
        f"route={route} cost={cost} map={costs_of(walked, 5)}",
        cost == walked[5] == costs_of(answer, 5),
    )

    audit_breaks = audit(lattice, 1, walked)
    second = Story(
        "the map audits silent: no edge still lowers a keyed node",
        f"breaks={audit_breaks}",
        audit_breaks == [],
    )

    corpus = synthetic(25, seed=11)
    drifted = sum(
        1 for graph in corpus if distances(graph, min(graph.nodes()))
        != relax_map(graph, min(graph.nodes()))
    )
    fourth = Story(
        "a seeded corpus agrees with the fixed point, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, step + 1)
    hopped = distances(chain, 0)
    fifth = Story(
        "a chain walks its whole length and stops at the door it owns",
        f"nodes={len(chain)} reached={len(hopped)} far={hopped[9]}",
        len(hopped) == len(chain) and hopped[9] == sum(range(1, 10)),
    )

    behind = Graph()
    for source, target, weight in ((1, 2, 3), (7, 8, 1)):
        behind.add_edge(source, target, weight)
    apart = distances(behind, 1)
    sixth = Story(
        "an island stays out of the map: omission is unreachable",
        f"keys={sorted(apart)} island={8 in apart}",
        8 not in apart and 7 not in apart and apart == {1: 0, 2: 3},
    )
    return [first, second, third, fourth, fifth, sixth]


def costs_of(costs: dict, node: int) -> object:
    """The map's answer for a node, or None when the map omits it."""
    return costs.get(node)
