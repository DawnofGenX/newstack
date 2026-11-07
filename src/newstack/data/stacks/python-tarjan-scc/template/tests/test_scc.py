from __future__ import annotations

import random

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    oracle_partition,
)
from {{ package_name }}.scc import (
    audit,
    condense,
    partition,
    strong_components,
)


def diamond() -> Graph:
    graph = Graph()
    for source, target in ((1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 4), (4, 6)):
        graph.add_edge(source, target)
    return graph


def test_the_walker_answers_the_oracle_on_the_diamond() -> None:
    assert partition(diamond()) == oracle_partition(diamond())


def test_the_published_spelling_matches_the_walk() -> None:
    assert strong_components(diamond()) == list(partition(diamond()))


def test_a_chain_walks_apart() -> None:
    graph = Graph()
    for step in range(9):
        graph.add_edge(step, step + 1)
    groups = partition(graph)
    assert len(groups) == 10
    assert all(len(group) == 1 for group in groups)
    assert groups == oracle_partition(graph)


def test_a_ring_walks_whole() -> None:
    graph = Graph()
    for step in range(8):
        graph.add_edge(step, (step + 1) % 8)
    assert partition(graph) == (frozenset(range(8)),)
    assert partition(graph) == oracle_partition(graph)


def test_two_rings_and_a_bridge() -> None:
    graph = Graph()
    for step in range(4):
        graph.add_edge(step, (step + 1) % 4)
    for step in range(10, 14):
        graph.add_edge(step, 10 + (step + 1 - 10) % 4)
    graph.add_edge(3, 10)
    assert partition(graph) == oracle_partition(graph)
    assert audit(graph, partition(graph)) == []


def test_every_node_lands_in_exactly_one_component() -> None:
    for graph in synthetic(40, seed=13):
        groups = partition(graph)
        seats = [member for group in groups for member in group]
        assert sorted(seats) == sorted(graph.nodes())
        assert len(seats) == len(set(seats))
        assert audit(graph, groups) == []


def test_the_walker_agrees_with_the_closure_on_every_graph() -> None:
    for graph in synthetic(60, seed=77):
        assert partition(graph) == oracle_partition(graph)


def test_random_tangles_agree_with_the_closure() -> None:
    rng = random.Random(2026)
    for _ in range(80):
        graph = Graph()
        labels = rng.sample(range(0, 999, 11), rng.randint(2, 10))
        for node in labels:
            graph.add_node(node)
        for _ in range(rng.randint(1, len(labels) * len(labels) // 2)):
            graph.add_edge(rng.choice(labels), rng.choice(labels))
        assert partition(graph) == oracle_partition(graph)


def test_the_fold_answers_heads_and_crossings() -> None:
    dag = condense(diamond())
    assert sorted(dag.nodes()) == [1, 4, 6]
    assert sorted(dag.edges()) == [(1, 4), (4, 6)]
    ring = Graph()
    for step in range(6):
        ring.add_edge(step, (step + 1) % 6)
    assert condense(ring).nodes() == (0,)
    assert condense(ring).edges() == ()


def test_the_fold_holds_across_every_seeded_graph() -> None:
    for graph in synthetic(30, seed=91):
        groups = partition(graph)
        heads = {min(group) for group in groups}
        assert set(condense(graph).nodes()) == heads
