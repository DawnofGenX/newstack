from __future__ import annotations

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    is_connected,
    load_graphs,
    report_lines,
    synthetic,
    write_graphs,
)
from {{ package_name }}.oracle import (
    min_cost,
)
from {{ package_name }}.solve import (
    tree_cost,
)


def test_the_generator_is_deterministic() -> None:
    first = [graph.to_text() for graph in synthetic(10, seed=5)]
    assert first == [graph.to_text() for graph in synthetic(10, seed=5)]


def test_every_generated_graph_is_one_piece() -> None:
    for graph in synthetic(20, seed=5):
        assert is_connected(graph)


def test_the_generated_edges_speak_their_weights() -> None:
    for graph in synthetic(6, seed=5):
        for edge_pair, weight in graph.edges():
            assert weight >= 0
            assert f"{edge_pair[0]}>{edge_pair[1]}={weight}" in graph.to_text()


def test_the_graphs_are_distinct() -> None:
    corpus = synthetic(15, seed=9)
    assert len({graph.to_text() for graph in corpus}) == 15


def test_a_generated_corpus_answers_the_enumeration() -> None:
    for graph in synthetic(12, seed=5):
        assert tree_cost(graph, min(graph.nodes())) == min_cost(graph)


def test_no_graphs_from_zero() -> None:
    try:
        synthetic(0)
    except CorpusError:
        pass
    else:
        raise AssertionError("zero asked for graphs, graphs arrived")


def test_a_snapshot_replays_its_graphs() -> None:
    corpus = synthetic(8, seed=5)
    frozen = Snapshot(tuple(graph.to_text() for graph in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert [graph.to_text() for graph in thawed.graphs()] == [
        graph.to_text() for graph in corpus
    ]


def test_half_a_snapshot_is_no_snapshot() -> None:
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        pass
    else:
        raise AssertionError("half a snapshot thawed")


def test_a_written_corpus_reads_back(tmp_path) -> None:
    corpus = synthetic(6, seed=3)
    path = tmp_path / "graphs.txt"
    write_graphs(corpus, str(path))
    assert [graph.to_text() for graph in load_graphs(str(path))] == [
        graph.to_text() for graph in corpus
    ]


def test_a_missing_corpus_is_named(tmp_path) -> None:
    try:
        load_graphs(str(tmp_path / "missing.txt"))
    except CorpusError:
        pass
    else:
        raise AssertionError("a missing corpus read as graphs")


def test_a_noisy_corpus_is_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\na > b\n", encoding="utf-8")
    try:
        load_graphs(str(noise))
    except CorpusError:
        pass
    else:
        raise AssertionError("noise parsed as a corpus")


def test_the_report_counts_every_graph() -> None:
    corpus = synthetic(10, seed=4)
    lines = report_lines(corpus)
    assert len(lines) == len(corpus)
    for line in lines:
        assert "equal=True" in line
