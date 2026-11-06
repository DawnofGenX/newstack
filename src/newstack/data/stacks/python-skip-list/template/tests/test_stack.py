from __future__ import annotations

import pytest

from {{ package_name }}.stack import (
    CorpusError,
    Snapshot,
    load_pairs,
    synthetic,
    write_pairs,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    assert synthetic(60, seed=5) != synthetic(60, seed=6)


def test_the_keys_arrive_distinct() -> None:
    pairs = synthetic(120, seed=2)
    assert len({key for key, _ in pairs}) == 120
    assert [value for _, value in pairs] == list(range(120))


def test_a_corpus_of_zero_is_no_corpus() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_stream_writes_and_reads_back(tmp_path) -> None:
    pairs = synthetic(30, seed=9)
    path = tmp_path / "pairs.txt"
    write_pairs(pairs, path)
    assert load_pairs(path) == pairs


def test_blanks_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# a header\n\n1 5\n\n", encoding="utf-8")
    assert load_pairs(path) == [(1, 5)]


def test_a_stream_of_noise_is_refused(tmp_path) -> None:
    path = tmp_path / "noise.txt"
    path.write_text("1 x\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_pairs(path)


def test_a_file_of_comments_holds_no_pairs(tmp_path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_pairs(path)


def test_a_missing_stream_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_pairs(tmp_path / "missing.txt")


def test_a_snapshot_replays_pairs_and_seed() -> None:
    frozen = Snapshot(synthetic(10, seed=4), 77)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.pairs == frozen.pairs
    assert thawed.seed == 77


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
