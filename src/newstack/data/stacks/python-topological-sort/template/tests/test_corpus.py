"""Corpora: the shipped fixture, the generator, snapshots in and out."""

from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_graphs,
    report_lines,
    synthetic,
    tangles,
    write_graphs,
)
from {{ package_name }}.cycle import cycle
from {{ package_name }}.oracle import naive_order
from {{ package_name }}.order import (
    block,
    order,
    validate,
)


def test_the_shipped_fixture_orders_and_validates():
    for graph in load_graphs("fixtures/graphs.txt"):
        listed = order(graph)
        assert cycle(graph) is None
        assert validate(graph, listed) == []
        assert listed == naive_order(graph)


def test_the_generator_is_deterministic():
    first = [graph.to_text() for graph in synthetic(10, seed=4)]
    assert first == [graph.to_text() for graph in synthetic(10, seed=4)]


def test_the_generator_orders_every_graph():
    for graph in synthetic(20, seed=DEFAULT_SEED):
        assert validate(graph, order(graph)) == []


def test_no_graphs_from_zero():
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_snapshot_replays_its_graphs():
    corpus = synthetic(6, seed=2)
    frozen = Snapshot(tuple(graph.to_text() for graph in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert [graph.to_text() for graph in thawed.graphs()] == [
        graph.to_text() for graph in corpus
    ]


def test_half_a_snapshot_is_no_snapshot():
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')


def test_a_written_corpus_reads_back(tmp_path):
    corpus = synthetic(5, seed=3)
    name = str(tmp_path / "graphs.txt")
    write_graphs(corpus, name)
    assert [graph.to_text() for graph in load_graphs(name)] == [
        graph.to_text() for graph in corpus
    ]


def test_a_missing_corpus_is_named(tmp_path):
    with pytest.raises(CorpusError):
        load_graphs(str(tmp_path / "missing.txt"))


def test_a_noisy_corpus_is_refused(tmp_path):
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\na > b\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_graphs(str(noise))


def test_the_report_counts_every_graph():
    corpus = synthetic(8, seed=1)
    assert len(report_lines(corpus)) == len(corpus)


def test_the_shipped_tangles_stay_tangled():
    for graph in tangles():
        assert cycle(graph) is not None
        assert block(graph)
