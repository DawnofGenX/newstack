from __future__ import annotations

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_graphs,
    reaches_all,
    report_lines,
    synthetic,
    write_graphs,
)
from {{ package_name }}.oracle import (
    distance_table,
)
from {{ package_name }}.solve import (
    distances,
)


def test_the_generator_is_deterministic() -> None:
    assert [g.to_text() for g in synthetic(6, seed=3)] == \
        [g.to_text() for g in synthetic(6, seed=3)]


def test_the_graphs_are_distinct() -> None:
    assert len({g.to_text() for g in synthetic(10, seed=3)}) == 10


def test_every_generated_graph_walks_on() -> None:
    assert all(reaches_all(graph) for graph in synthetic(8, seed=4))


def test_the_seed_default_is_spoken() -> None:
    assert DEFAULT_SEED > 0


def test_a_written_corpus_reads_back(tmp_path) -> None:
    corpus = synthetic(4, seed=9)
    path_name = str(tmp_path / "graphs.txt")
    write_graphs(corpus, path_name)
    assert [g.to_text() for g in load_graphs(path_name)] == \
        [g.to_text() for g in corpus]


def test_a_missing_corpus_is_named(tmp_path) -> None:
    try:
        load_graphs(str(tmp_path / "missing.txt"))
    except CorpusError:
        pass
    else:
        raise AssertionError("a missing corpus read graphs")


def test_a_noisy_corpus_is_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\na > b\n", encoding="utf-8")
    try:
        load_graphs(str(noise))
    except CorpusError:
        pass
    else:
        raise AssertionError("noise read graphs")


def test_a_snapshot_replays_its_graphs() -> None:
    corpus = synthetic(4, seed=8)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert [g.to_text() for g in thawed.graphs()] == [g.to_text() for g in corpus]


def test_half_a_snapshot_is_no_snapshot() -> None:
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        pass
    else:
        raise AssertionError("half a snapshot thawed")


def test_no_graphs_from_zero() -> None:
    try:
        synthetic(0)
    except CorpusError:
        pass
    else:
        raise AssertionError("zero grew graphs")


def test_the_report_counts_every_graph() -> None:
    corpus = synthetic(6, seed=2)
    assert len(report_lines(corpus)) == 6


def test_the_report_lines_agree_with_the_walk() -> None:
    for line, graph in zip(report_lines(synthetic(6, seed=2)), synthetic(6, seed=2),
                           strict=False):
        assert "True" in line
        assert distances(graph) == distance_table(graph)
