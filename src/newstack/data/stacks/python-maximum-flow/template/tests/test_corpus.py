from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    has_route,
    load_graphs,
    report_lines,
    synthetic,
    write_graphs,
)
from {{ package_name }}.oracle import (
    min_cut,
)
from {{ package_name }}.solve import (
    max_flow,
)


def test_the_generator_is_deterministic() -> None:
    assert [g.to_text() for g in synthetic(12, seed=5)] == [
        g.to_text() for g in synthetic(12, seed=5)
    ]


def test_the_generated_networks_are_distinct() -> None:
    assert len({g.to_text() for g in synthetic(12, seed=5)}) == 12


def test_every_generated_network_answers_the_enumeration() -> None:
    for graph in synthetic(12, seed=5):
        source, sink = min(graph.nodes()), max(graph.nodes())
        assert max_flow(graph, source, sink) == min_cut(graph, source, sink)


def test_no_networks_from_zero() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_snapshot_replays_its_networks() -> None:
    corpus = synthetic(6, seed=3)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    assert [g.to_text() for g in Snapshot.loads(frozen.dumps()).graphs()] == [
        g.to_text() for g in corpus
    ]


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')


def test_a_written_corpus_reads_back(tmp_path) -> None:
    corpus = synthetic(6, seed=3)
    path_name = str(tmp_path / "networks.txt")
    write_graphs(corpus, path_name)
    assert [g.to_text() for g in load_graphs(path_name)] == [g.to_text() for g in corpus]


def test_a_missing_corpus_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_graphs(str(tmp_path / "missing.txt"))


def test_a_noisy_corpus_is_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\na > b\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_graphs(str(noise))


def test_the_report_counts_every_network() -> None:
    corpus = synthetic(9, seed=4)
    lines = report_lines(corpus)
    assert len(lines) == len(corpus)
    assert all("cut" in line for line in lines)


def test_a_route_walks_when_one_is_owed() -> None:
    graph = synthetic(1, seed=1)[0]
    assert has_route(graph, min(graph.nodes()), max(graph.nodes()))
