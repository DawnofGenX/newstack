"""The tangle named: deterministic DFS, None when nothing tangles."""

from __future__ import annotations

from {{ package_name }}.corpus import synthetic, tangles
from {{ package_name }}.cycle import cycle
from {{ package_name }}.graph import Graph


def test_a_ladder_answers_clear():
    graph = Graph()
    for source, target in ((1, 2), (2, 3), (1, 3)):
        graph.add_edge(source, target)
    assert cycle(graph) is None


def test_a_ring_names_its_ring():
    ring = Graph().add_edge(4, 5).add_edge(5, 6).add_edge(6, 4)
    assert cycle(ring) == (4, 5, 6)


def test_a_tangle_names_a_cycle():
    for graph in tangles():
        assert cycle(graph) is not None


def test_the_answer_is_a_fixed_point():
    for graph in tangles():
        assert cycle(graph) == cycle(graph)


def test_a_seeded_corpus_answers_clear():
    for graph in synthetic(20, seed=9):
        assert cycle(graph) is None
