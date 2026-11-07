from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    synthetic,
    write_texts,
)


def test_the_generator_is_deterministic_and_distinct() -> None:
    assert synthetic(15, seed=3) == synthetic(15, seed=3)
    assert len(set(synthetic(15, seed=3))) == 15
    assert synthetic(15, seed=3) == sorted(synthetic(15, seed=3))


def test_no_texts_come_from_zero() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_written_list_reads_back(tmp_path) -> None:
    corpus = synthetic(6, seed=11)
    path = tmp_path / "texts.txt"
    write_texts(corpus, str(path))
    assert load_texts(str(path)) == corpus


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "texts.txt"
    path.write_text("# a comment\n\nbanana\n", encoding="utf-8")
    assert load_texts(str(path)) == ["banana"]


def test_noise_and_emptiness_are_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("banana\nBanana\n", encoding="utf-8")
    with pytest.raises(CorpusError, match=r"non-letter|lowercase"):
        load_texts(str(noise))
    blank = tmp_path / "blank.txt"
    blank.write_text("# nothing\n\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="no texts"):
        load_texts(str(blank))
    with pytest.raises(CorpusError, match="no such text list"):
        load_texts(str(tmp_path / "missing.txt"))


def test_a_snapshot_replays_its_texts() -> None:
    corpus = synthetic(4, seed=8)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.texts) == corpus
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
    with pytest.raises(CorpusError):
        Snapshot.loads("not json")
