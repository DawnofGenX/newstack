"""Six stories about carried flow, every number computed live.

A story states a promise the walker owes the cut enumeration and
answers it against the real modules - no hand-written
expectations, no stored figures. If any story stops holding, the
tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .graph import Graph
from .oracle import min_cut
from .solve import audit, flow_map, max_flow


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _diamond() -> Graph:
    graph = Graph()
    for start, end, room in (
        (0, 1, 3), (1, 3, 2), (0, 2, 2), (2, 3, 3), (0, 3, 1), (1, 2, 1),
    ):
        graph.add_edge(start, end, room)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    diamond = _diamond()
    walked = max_flow(diamond, 0, 3)
    least = min_cut(diamond, 0, 3)
    first = Story(
        "the walker answers the enumeration's least, value for value",
        f"walked={walked} cut={least} equal={walked == least}",
        walked == least,
    )

    shipped = flow_map(diamond, 0, 3)
    breaks = audit(diamond, 0, 3, shipped)
    second = Story(
        "the map conserves inside and never ships past a capacity",
        f"arcs={len(shipped)} breaks={breaks}",
        breaks == [],
    )

    again = flow_map(diamond, 0, 3)
    third = Story(
        "the same network walks to the same map, run after run",
        f"shipped={sorted(shipped.items())} stable={shipped == again}",
        shipped == again,
    )

    corpus = synthetic(20, seed=11)
    drifted = sum(
        1 for graph in corpus
        if max_flow(graph, min(graph.nodes()), max(graph.nodes()))
        != min_cut(graph, min(graph.nodes()), max(graph.nodes()))
    )
    fourth = Story(
        "a seeded corpus answers the enumeration's least, network after network",
        f"networks={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    carried = max_flow(chain, 0, 8)
    fifth = Story(
        "a chain carries its least door: every door is the only door",
        f"nodes={len(chain)} flow={carried} least={min_cut(chain, 0, 8)}",
        carried == min_cut(chain, 0, 8) == 1,
    )

    apart = Graph()
    apart.add_edge(1, 2, 4)
    apart.add_edge(7, 8, 1)
    sixth = Story(
        "a network with no route carries zero, and says zero",
        f"flow={max_flow(apart, 1, 8)} cut={min_cut(apart, 1, 8)}",
        max_flow(apart, 1, 8) == min_cut(apart, 1, 8) == 0,
    )
    return [first, second, third, fourth, fifth, sixth]
