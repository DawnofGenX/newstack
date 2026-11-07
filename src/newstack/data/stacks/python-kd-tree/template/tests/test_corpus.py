from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    DEFAULT_SPAN,
    CorpusError,
    Snapshot,
    load_points,
    parse_point,
    synthetic,
    write_points,
)

SEEDS = (7, 23, 91, 1009)


def test_the_generator_is_deterministic_distinct_and_sorted() -> None:
    for seed in SEEDS:
        corpus = synthetic(80, seed=seed)
        assert corpus == synthetic(80, seed=seed)
        assert len(set(corpus)) == 80
        assert corpus == sorted(corpus)


def test_the_gate_of_a_corpus() -> None:
    for bad in (0, -4):
        with pytest.raises(CorpusError):
            synthetic(bad)
    with pytest.raises(CorpusError):
        synthetic(10, span=2)


def test_a_pair_in_text_becomes_a_pair_of_integers() -> None:
    assert parse_point("3,-4") == (3, -4)
    for bad in ("1", "1,2,3", "1.5,2", "a,b", ""):
        with pytest.raises(CorpusError):
            parse_point(bad)


def test_a_point_list_round_trips(tmp_path) -> None:
    corpus = synthetic(40, seed=5)
    path = str(tmp_path / "points.txt")
    write_points(corpus, path)
    assert load_points(path) == corpus


def test_a_list_skips_comments_and_blanks(tmp_path) -> None:
    path = tmp_path / "noisy.txt"
    path.write_text("# a comment\n\n1,2\n   \n3,4\n", encoding="utf-8")
    assert load_points(str(path)) == [(1, 2), (3, 4)]


def test_a_broken_list_is_refused_by_name(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_points(str(tmp_path / "missing.txt"))
    noise = tmp_path / "noise.txt"
    noise.write_text("# only comments\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_points(str(noise))
    bad = tmp_path / "bad.txt"
    bad.write_text("1,2,3\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_points(str(bad))


def test_a_snapshot_replays_its_corpus_and_seed() -> None:
    corpus = synthetic(30, seed=DEFAULT_SEED)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.points) == corpus
    assert thawed.seed == DEFAULT_SEED
    for broken in ('{"seed": 1}', '{"points": []}', "not json"):
        with pytest.raises(CorpusError):
            Snapshot.loads(broken)


def test_the_defaults_are_the_ones_the_storms_use() -> None:
    assert DEFAULT_SPAN >= 100
    corpus = synthetic(50)
    assert corpus == synthetic(50, seed=DEFAULT_SEED)
