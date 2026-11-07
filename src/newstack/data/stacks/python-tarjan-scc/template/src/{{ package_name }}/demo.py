"""Six stories about components, every number computed live.

A story states a promise the walker owes the oracle and answers it
against the real modules - no hand-written expectations, no stored
figures. If any story stops holding, the tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .cycle import has_cycle
from .graph import Graph
from .oracle import oracle_partition
from .scc import audit, condense, partition


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _diamond() -> Graph:
    graph = Graph()
    for source, target in ((1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 4), (4, 6)):
        graph.add_edge(source, target)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    diamond = _diamond()
    groups = partition(diamond)
    answer = oracle_partition(diamond)
    first = Story(
        "the walker answers the oracle, component for component",
        f"walked={len(groups)} oracle={len(answer)} equal={groups == answer}",
        groups == answer,
    )

    seats = [member for group in groups for member in group]
    second = Story(
        "every node lands in exactly one component",
        f"nodes={len(diamond)} seats={len(seats)} quiet={audit(diamond, groups) == []}",
        audit(diamond, groups) == [] and sorted(seats) == sorted(diamond.nodes()),
    )

    dag = condense(diamond)
    third = Story(
        "the condensed graph is a graph the cycle checker clears",
        f"heads={sorted(dag.nodes())} edges={len(dag.edges())} cycle={has_cycle(dag)}",
        has_cycle(dag) is None and len(dag) == len(groups),
    )

    corpus = synthetic(25, seed=11)
    drifted = sum(1 for graph in corpus if partition(graph) != oracle_partition(graph))
    fourth = Story(
        "a seeded corpus agrees with the closure, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1)
    singles = partition(chain)
    fifth = Story(
        "a chain walks apart into honest singletons",
        f"nodes={len(chain)} components={len(singles)} "
        f"all_alone={all(len(group) == 1 for group in singles)}",
        len(singles) == len(chain) and all(len(group) == 1 for group in singles),
    )

    ring = Graph()
    for step in range(8):
        ring.add_edge(step, (step + 1) % 8)
    whole = partition(ring)
    sixth = Story(
        "a ring walks whole: one component, the oracle agrees",
        f"nodes=8 components={len(whole)} equal={whole == oracle_partition(ring)}",
        len(whole) == 1 and next(iter(whole)) == frozenset(range(8))
        and whole == oracle_partition(ring),
    )
    return [first, second, third, fourth, fifth, sixth]
