from __future__ import annotations

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_graphs,
    report_lines,
    synthetic,
    write_graphs,
)
from {{ package_name }}.oracle import (
    relax_map,
)
from {{ package_name }}.solve import (
    distances,
)


def test_the_generator_is_deterministic() -> None:
    first = [graph.to_text() for graph in synthetic(10, seed=5)]
    assert first == [graph.to_text() for graph in synthetic(10, seed=5)]


def test_the_generated_edges_speak_their_weights() -> None:
    for graph in synthetic(6, seed=5):
        for source, target, weight in graph.edges():
            assert weight >= 0
            assert f"{source}>{target}={weight}" in graph.to_text()


def test_the_graphs_are_distinct() -> None:
    corpus = synthetic(15, seed=9)
    assert len({graph.to_text() for graph in corpus}) == 15


def test_a_seeded_corpus_holds_an_unreachable_somewhere() -> None:
    honest = sum(
        len(distances(graph, min(graph.nodes()))) < len(graph)
        for graph in synthetic(20, seed=5)
    )
    assert honest > 0


def test_no_graphs_from_zero() -> None:
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero made graphs")


def test_a_written_corpus_reads_back(tmp_path) -> None:
    corpus = synthetic(6, seed=3)
    path = str(tmp_path / "graphs.txt")
    write_graphs(corpus, path)
    assert [g.to_text() for g in load_graphs(path)] == [g.to_text() for g in corpus]


def test_a_missing_corpus_is_named(tmp_path) -> None:
    try:
        load_graphs(str(tmp_path / "missing.txt"))
    except CorpusError:
        return
    raise AssertionError("a missing file answered")


def test_a_noisy_corpus_is_refused(tmp_path) -> None:
    path = tmp_path / "noise.txt"
    path.write_text("# comment\n\na > b\n", encoding="utf-8")
    try:
        load_graphs(str(path))
    except CorpusError:
        return
    raise AssertionError("noise passed as a graph")


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# header\n\n1 2 1>2=4\n\n", encoding="utf-8")
    assert [g.to_text() for g in load_graphs(str(path))] == ["1 2 1>2=4"]


def test_a_snapshot_replays_its_graphs() -> None:
    corpus = synthetic(4, seed=1)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert [g.to_text() for g in thawed.graphs()] == [g.to_text() for g in corpus]


def test_half_a_snapshot_is_no_snapshot() -> None:
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        return
    raise AssertionError("half a snapshot thawed")


def test_the_report_counts_every_graph() -> None:
    corpus = synthetic(8, seed=2)
    assert len(report_lines(corpus)) == 8


def test_the_generated_corpora_answer_the_fixed_point() -> None:
    for graph in synthetic(20, seed=DEFAULT_SEED):
        source = min(graph.nodes())
        assert distances(graph, source) == relax_map(graph, source)
