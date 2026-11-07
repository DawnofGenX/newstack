from __future__ import annotations

from tempfile import TemporaryDirectory

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_graphs,
    report_lines,
    synthetic,
    write_graphs,
)


def test_the_generator_is_deterministic() -> None:
    assert [g.to_text() for g in synthetic(8, seed=5)] == [
        g.to_text() for g in synthetic(8, seed=5)
    ]


def test_a_differing_seed_owes_a_differing_corpus() -> None:
    assert [g.to_text() for g in synthetic(8, seed=5)] != [
        g.to_text() for g in synthetic(8, seed=6)
    ]


def test_the_generator_answers_its_count() -> None:
    assert len(synthetic(9, seed=3)) == 9
    assert len({g.to_text() for g in synthetic(9, seed=3)}) == 9


def test_generated_graphs_settle_the_walk() -> None:
    from {{ package_name }}.walk import (
        settled,
    )

    for graph in synthetic(15, seed=DEFAULT_SEED):
        assert not settled(graph, graph.nodes()[0])


def test_no_count_is_answered_for_zero_graphs() -> None:
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero graphs were counted")


def test_a_written_corpus_reads_back() -> None:
    corpus = synthetic(6, seed=4)
    with TemporaryDirectory() as room:
        path = f"{room}/graphs.txt"
        write_graphs(corpus, path)
        assert [g.to_text() for g in load_graphs(path)] == [
            g.to_text() for g in corpus
        ]


def test_a_missing_corpus_is_named() -> None:
    try:
        load_graphs("/no/such/corpus.txt")
    except CorpusError:
        return
    raise AssertionError("a missing corpus answered")


def test_a_noisy_corpus_is_refused() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/noise.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# comment\n\na > b\n")
        try:
            load_graphs(path)
        except CorpusError:
            return
    raise AssertionError("noise parsed as a corpus")


def test_comments_and_blanks_are_skipped() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/quiet.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# note\n\n1 2 1>2=-3\n\n# end\n")
        graphs = load_graphs(path)
    assert len(graphs) == 1
    assert graphs[0].edges() == ((1, 2, -3),)


def test_a_snapshot_survives_its_face() -> None:
    corpus = synthetic(4, seed=8)
    frozen = Snapshot(tuple(g.to_text() for g in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.seed == DEFAULT_SEED
    assert [g.to_text() for g in thawed.graphs()] == [g.to_text() for g in corpus]


def test_half_a_snapshot_is_no_snapshot() -> None:
    for noise in ('{"seed": 1}', "not json", '{"graphs": []}'):
        try:
            Snapshot.loads(noise)
        except CorpusError:
            continue
        raise AssertionError(f"{noise!r} thawed")


def test_the_report_counts_every_graph() -> None:
    corpus = synthetic(7, seed=2)
    lines = report_lines(corpus)
    assert len(lines) == 7
    assert all("settled True" in line for line in lines)
